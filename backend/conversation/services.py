import logging
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from livekit.api import AccessToken, VideoGrants

from .models import Session

logger = logging.getLogger(__name__)

DEFAULT_TOKEN_TTL_SECONDS = 600


def _child_livekit_token(child_profile, room_name, ttl_seconds=None):
    """Mint a LiveKit JWT for the child to join ``room_name``.

    ttl_seconds shortens the token life (the demo guards pass the session limit plus a
    margin) so a leaked token cannot be used to join much later. None means 10 minutes
    (the token is only needed to connect; LiveKit refreshes it for the open connection),
    never the library's 6 hour default.
    """
    token = (
        AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(f"child_{child_profile.user_id}")
        .with_grants(VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        ))
    )
    return token.with_ttl(timedelta(seconds=ttl_seconds or DEFAULT_TOKEN_TTL_SECONDS)).to_jwt()


def start_session(child_profile, token_ttl_seconds=None):
    """Create a fresh active session and return a LiveKit token.

    If a previous active session exists, close it first so reporting runs
    instead of silently re-entering a stale room after reload/navigation.
    """
    active = Session.objects.filter(child=child_profile, status='active').first()
    if active:
        logger.info(
            "Ending existing active session before starting fresh: session_id=%s, room=%s",
            active.id,
            active.livekit_room_name,
        )
        end_session(active)

    # livekit_room_name is unique, so a blank placeholder would collide when two
    # sessions start in the same instant (both rows hold '' until the next line).
    # A unique throwaway name is written first; the final name is unchanged.
    session = Session.objects.create(
        child=child_profile,
        status='active',
        livekit_room_name=f"pending_{uuid.uuid4().hex}",
    )
    room_name = f"session_{session.id}"
    session.livekit_room_name = room_name
    session.save(update_fields=['livekit_room_name'])

    try:
        from gamification.services import evaluate_badges, update_streak

        streak = update_streak(child_profile)
        if streak['extended']:
            evaluate_badges(child_profile)
    except Exception:
        logger.exception(
            "Streak update failed for child_id=%s (session continues)",
            child_profile.id,
        )

    jwt_token = _child_livekit_token(child_profile, room_name, token_ttl_seconds)
    logger.info("Session started: session_id=%s, room=%s", session.id, room_name)
    return session, jwt_token, True


def end_session(session):
    """End a session: mark closed, then run LLM reporting pipeline in a background thread."""
    if session.status == 'ended':
        return

    with transaction.atomic():
        session.status = 'ended'
        session.ended_at = timezone.now()
        session.save(update_fields=['status', 'ended_at'])

    from reporting.services import run_post_session_pipeline

    run_post_session_pipeline(session.id)
    logger.info("Session ended: session_id=%s (post-session pipeline scheduled)", session.id)
