import logging
import math
from datetime import timedelta

from django.conf import settings
from django.db.models import Max
from django.shortcuts import get_object_or_404
from livekit.api import TokenVerifier, WebhookReceiver
from rest_framework import generics, status
from rest_framework.exceptions import Throttled
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import ParentChildLink
from authentication.permissions import IsChild, IsParent
from demo.accounts import is_judge_user
from . import demo_guards
from .models import Message, Session
from .serializers import MessageSerializer, ParentSessionSummarySerializer
from .services import start_session, end_session
from config.throttling import SharedUserRateThrottle
from .throttles import SessionStartThrottle, StartSessionRateThrottle

logger = logging.getLogger(__name__)


def _preferred_text(message: dict, child_profile) -> str:
    """The message in the child's language (Arabic first when unknown)."""
    lang = (getattr(child_profile, 'language_preference', '') or 'ar').lower()
    return message['en'] if lang.startswith('en') else message['ar']


def _denied_response(code, message, http_status, child_profile, headers=None):
    return Response(
        {'detail': _preferred_text(message, child_profile), 'code': code, 'message': message},
        status=http_status,
        headers=headers,
    )


class StartSessionView(APIView):
    """Child starts a new conversation session; receives a LiveKit token.

    Demo guards (conversation/demo_guards.py, no-ops while the guards are off):
    - 429 code=rate_limited      more than DEMO_SESSION_START_PER_HOUR starts in an hour
    - 429 code=daily_limit       the child used DEMO_DAILY_SESSIONS today (judge accounts:
                                 JUDGE_DAILY_SESSIONS, and JUDGE_SESSION_START_PER_HOUR above)
    - 503 code=voice_off         the operator's kill switch (VOICE_MODE=off)
    Every refusal carries message={ar, en}. A success carries voice_mode (eleven | xai |
    text), notice (set when the voice is resting: show it and chat by text), max_seconds and
    session_ends_at (null when there is no limit).
    """
    permission_classes = [IsAuthenticated, IsChild]
    throttle_classes = [SharedUserRateThrottle, StartSessionRateThrottle, SessionStartThrottle]

    def throttled(self, request, wait):
        exc = Throttled(detail={
            'detail': _preferred_text(demo_guards.message_for('rate_limited'),
                                      request.user.child_profile),
            'code': 'rate_limited',
            'message': demo_guards.message_for('rate_limited'),
        })
        exc.wait = math.ceil(wait) if wait else None
        raise exc

    def post(self, request):
        child_profile = request.user.child_profile
        judge = is_judge_user(request.user)
        try:
            text_only = str(request.data.get('text_only', '')).strip().lower() in ('1', 'true')
            grant = demo_guards.check_session_start(child_profile.id, text_only=text_only,
                                                    judge=judge)
        except demo_guards.GuardDenied as denied:
            return _denied_response(denied.code, denied.message, denied.http_status,
                                    child_profile)

        try:
            session, token, created = start_session(
                child_profile,
                token_ttl_seconds=(grant.max_seconds + 120) if grant.max_seconds else None,
            )
        except Exception:
            if grant.reserved:
                demo_guards.release_daily_session(child_profile.id, judge=judge)
            raise
        demo_guards.save_session_state(session.id, grant)

        notice = None
        if grant.decision.notice:
            notice = {'code': grant.decision.notice,
                      **demo_guards.message_for(grant.decision.notice)}
        ends_at = (session.started_at + timedelta(seconds=grant.max_seconds)
                   if grant.max_seconds else None)
        return Response(
            {
                'session_id': session.id,
                'livekit_token': token,
                'livekit_room_name': session.livekit_room_name,
                'livekit_url': settings.LIVEKIT_PUBLIC_URL,
                'voice_mode': grant.decision.mode,
                'notice': notice,
                'max_seconds': grant.max_seconds or None,
                'session_ends_at': ends_at.isoformat() if ends_at else None,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class EndSessionView(APIView):
    """Child explicitly ends their active session."""
    permission_classes = [IsAuthenticated, IsChild]

    def post(self, request, session_id):
        session = get_object_or_404(
            Session,
            id=session_id,
            child=request.user.child_profile,
        )
        end_session(session)
        return Response({'detail': 'Session ended.'})


class SessionMessagesView(generics.ListAPIView):
    """Fetch messages for a session (chat history for reconnection)."""
    permission_classes = [IsAuthenticated, IsChild]
    serializer_class = MessageSerializer

    def get_queryset(self):
        return Message.objects.filter(
            session_id=self.kwargs['session_id'],
            session__child=self.request.user.child_profile,
        ).order_by('created_at')


class LiveKitWebhookView(APIView):
    """Receives webhook events from the LiveKit server.

    Verifies signature — no JWT auth. Used as a fallback to end
    sessions when rooms close (child disconnects without clicking end).
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    # Every request is verified with the LiveKit signature (bad ones get 401), so the
    # anonymous 30/min throttle only ever dropped real room_finished / participant_left
    # events, which left sessions open (no parent report, StartSessionView reusing them).
    throttle_classes = []

    def post(self, request):
        auth_header = request.headers.get('Authorization', '')
        raw_body = request.body.decode()

        token_verifier = TokenVerifier(
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        )
        receiver = WebhookReceiver(token_verifier)
        try:
            event = receiver.receive(raw_body, auth_header)
        except Exception:
            logger.warning("Invalid LiveKit webhook signature")
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if not event.room:
            return Response(status=status.HTTP_200_OK)

        if event.event == 'room_finished':
            room_name = event.room.name
            try:
                session = Session.objects.get(
                    livekit_room_name=room_name,
                    status='active',
                )
                end_session(session)
                logger.info("Session ended via webhook: room=%s", room_name)
            except Session.DoesNotExist:
                logger.debug("room_finished webhook: no active session for room=%s (likely already closed)", room_name)

        elif event.event == 'participant_left':
            participant = event.participant
            if participant and not participant.identity.startswith('agent-'):
                room_name = event.room.name
                try:
                    session = Session.objects.get(
                        livekit_room_name=room_name,
                        status='active',
                    )
                    end_session(session)
                    logger.info(
                        "Session ended via participant_left webhook: room=%s, participant=%s",
                        room_name,
                        participant.identity,
                    )
                except Session.DoesNotExist:
                    logger.debug(
                        "participant_left webhook: no active session for room=%s, participant=%s",
                        room_name,
                        participant.identity,
                    )

        return Response(status=status.HTTP_200_OK)


class ParentChildConversationSummaryView(APIView):
    """Parent-only: recent sessions + snippets for one linked child."""

    permission_classes = [IsAuthenticated, IsParent]

    def get(self, request, child_id):
        parent = request.user.parent_profile
        try:
            link = ParentChildLink.objects.select_related('child__user').get(
                parent=parent,
                child_id=child_id,
                consent_status='approved',
            )
        except ParentChildLink.DoesNotExist:
            return Response(
                {'detail': 'Child not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        child = link.child
        sessions = Session.objects.filter(child=child).order_by('-started_at')[:15]
        session_data = ParentSessionSummarySerializer(sessions, many=True).data

        last_msg = Message.objects.filter(session__child=child).aggregate(
            m=Max('created_at')
        )['m']
        last_sess = Session.objects.filter(child=child).aggregate(
            m=Max('started_at')
        )['m']
        candidates = [t for t in (last_msg, last_sess) if t is not None]
        last_activity_at = max(candidates) if candidates else None

        return Response(
            {
                'child': {
                    'id': child.id,
                    'nickname': child.nickname,
                    'username': child.user.username,
                },
                'last_activity_at': last_activity_at,
                'sessions': session_data,
            }
        )
