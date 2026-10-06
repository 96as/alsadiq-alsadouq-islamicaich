"""Parent-facing reporting API views."""
from datetime import timedelta

from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import ParentChildLink
from authentication.permissions import IsParent
from gamification.models import ChildBadge, ChildQuestProgress, ChildStreak, PointsEvent
from gamification.services import gamification_state
from .models import WeeklySummary
from .services import (
    NOT_SCHOLAR_REVIEWED_LABEL,
    NO_SOURCES_LABEL,
    QUESTIONS_TITLE,
    REVIEWED_LABEL,
    SOURCES_FOOTER,
    SUGGESTED_TOPICS_LABEL,
    SUMMARY_LABEL,
    TRUST_LINE,
    questions_to_discuss,
    session_has_no_parent_flag,
    weekly_sources,
)
from .values_week import values_this_week


def _linked_child_or_none(parent, child_id):
    link = ParentChildLink.objects.filter(
        parent=parent, child_id=child_id, consent_status='approved',
    ).select_related('child').first()
    return link.child if link else None


class ChildInsightsView(APIView):
    """GET /api/reporting/insights/<child_id>/

    Latest weekly summary plus a short history, badges (with categories),
    and the child's level/streak snapshot.
    """
    permission_classes = [IsAuthenticated, IsParent]

    def get(self, request, child_id):
        parent = request.user.parent_profile
        child = _linked_child_or_none(parent, child_id)
        if not child:
            return Response({'detail': 'Child not linked.'}, status=403)

        summaries = list(
            WeeklySummary.objects
            .filter(child_id=child_id, parent=parent)
            .order_by('-week_start')[:4]
        )
        ws = summaries[0] if summaries else None

        badges = [
            {
                'name': cb.badge.name,
                'category': cb.badge.category,
                'icon': cb.badge.icon,
                'earned_at': cb.earned_at.isoformat(),
            }
            for cb in (
                ChildBadge.objects
                .filter(child_id=child_id)
                .select_related('badge')
                .order_by('-earned_at')
            )
        ]

        data = {
            'summary': ws.summary if ws else '',
            'suggested_topics': (ws.suggested_topics or []) if ws else [],
            'week_start': ws.week_start.isoformat() if ws else None,
            'badges': [b['name'] for b in badges],  # backwards-compatible shape
            'badges_detailed': badges,
            'history': [
                {
                    'week_start': s.week_start.isoformat(),
                    'summary': s.summary,
                    'suggested_topics': s.suggested_topics or [],
                }
                for s in summaries
            ],
            'gamification': gamification_state(child),
            # Database-only (ServedReference / TurnAudit); no child text.
            'sources': weekly_sources(child),
            'values_this_week': values_this_week(child),
            'questions_to_discuss': questions_to_discuss(child),
            'trust_line': TRUST_LINE,
            'summary_label': SUMMARY_LABEL,
            'labels': {
                'values_this_week': {'en': 'Values this week', 'ar': 'قيم هذا الأسبوع'},
                'suggested_topics': SUGGESTED_TOPICS_LABEL,
                'reviewed': REVIEWED_LABEL,
                'not_scholar_reviewed': NOT_SCHOLAR_REVIEWED_LABEL,
                'sources_footer': SOURCES_FOOTER,
                'no_sources': NO_SOURCES_LABEL,
                'questions_title': QUESTIONS_TITLE,
            },
        }
        return Response(data)


# Parents never see the stored PointsEvent.reason: for conversation points it is wording the
# LLM wrote and could paraphrase something the child disclosed. Fixed bilingual labels only.
_POINTS_LABELS = {
    'quest': 'Quest completed / إكمال مهمة',
    'streak': 'Daily streak bonus / مكافأة المواظبة اليومية',
    'badge': 'Badge earned / وسام جديد',
    'adjustment': 'Points adjustment / تعديل النقاط',
}
_ENGAGEMENT_LABELS = {
    'excellent': 'Excellent conversation / محادثة ممتازة',
    'good': 'Good conversation / محادثة جيدة',
    'poor': 'Conversation needed a redirect / محادثة احتاجت إلى توجيه',
    'bad': 'Conversation needed a redirect / محادثة احتاجت إلى توجيه',
}


def _safe_points_reason(event) -> str:
    if event.source != 'conversation':
        return _POINTS_LABELS.get(event.source, _POINTS_LABELS['adjustment'])
    from gamification.services import ENGAGEMENT_DELTAS

    for quality, delta in ENGAGEMENT_DELTAS.items():
        if delta == event.delta:
            return _ENGAGEMENT_LABELS[quality]
    return _POINTS_LABELS['adjustment']


class ChildActivityDashboardView(APIView):
    """GET /api/reporting/dashboard/<child_id>/

    Aggregated activity stats for one linked child: sessions, talk time,
    streak, level, quest pipeline, badges, and a 14-day points timeline.
    """
    permission_classes = [IsAuthenticated, IsParent]

    def get(self, request, child_id):
        from conversation.models import Session

        parent = request.user.parent_profile
        child = _linked_child_or_none(parent, child_id)
        if not child:
            return Response({'detail': 'Child not linked.'}, status=403)

        now = timezone.now()
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())  # Monday

        ended_sessions = Session.objects.filter(child=child, status='ended')
        sessions_total = ended_sessions.count()
        week_sessions = list(
            ended_sessions.filter(started_at__date__gte=week_start)
            .values('started_at', 'ended_at')
        )
        week_seconds = sum(
            (s['ended_at'] - s['started_at']).total_seconds()
            for s in week_sessions
            if s['ended_at']
        )

        quest_counts = {
            'completed': 0,
            'pending_verification': 0,
            'in_progress': 0,
            'not_started': 0,
        }
        for row in (
            ChildQuestProgress.objects
            .filter(child=child)
            .values_list('status', flat=True)
        ):
            if row in quest_counts:
                quest_counts[row] += 1

        streak = ChildStreak.objects.filter(child=child).first()

        recent_badges = [
            {
                'name': cb.badge.name,
                'category': cb.badge.category,
                'icon': cb.badge.icon,
                'earned_at': cb.earned_at.isoformat(),
            }
            for cb in (
                ChildBadge.objects
                .filter(child=child)
                .select_related('badge')
                .order_by('-earned_at')[:5]
            )
        ]
        badges_total = ChildBadge.objects.filter(child=child).count()

        timeline_start = today - timedelta(days=13)
        daily = {
            row['day'].isoformat(): row['points']
            for row in (
                PointsEvent.objects
                .filter(child=child, created_at__date__gte=timeline_start)
                .annotate(day=TruncDate('created_at'))
                .values('day')
                .annotate(points=Sum('delta'))
            )
        }
        points_timeline = [
            {
                'date': (timeline_start + timedelta(days=i)).isoformat(),
                'points': daily.get(
                    (timeline_start + timedelta(days=i)).isoformat(), 0
                ),
            }
            for i in range(14)
        ]

        quiet_session_ids = {}
        recent_activity = []
        for e in (
            PointsEvent.objects
            .filter(child=child)
            .select_related('session')
            .order_by('-created_at')[:10]
        ):
            if e.session_id is None:
                quiet = False
            else:
                if e.session_id not in quiet_session_ids:
                    quiet_session_ids[e.session_id] = session_has_no_parent_flag(e.session)
                quiet = quiet_session_ids[e.session_id]
            recent_activity.append({
                'delta': e.delta,
                # a no-parent-notify session shows no wording at all
                'reason': '' if quiet else _safe_points_reason(e),
                'source': e.source,
                'created_at': e.created_at.isoformat(),
            })

        return Response({
            'nickname': child.nickname,
            'generated_at': now.isoformat(),
            'sessions': {
                'total': sessions_total,
                'this_week': len(week_sessions),
                'talk_minutes_this_week': int(week_seconds // 60),
            },
            'streak': {
                'current': streak.current_streak if streak else 0,
                'longest': streak.longest_streak if streak else 0,
                'last_active_date': (
                    streak.last_active_date.isoformat()
                    if streak and streak.last_active_date else None
                ),
            },
            'level': gamification_state(child),
            'quests': quest_counts,
            'badges': {
                'total': badges_total,
                'recent': recent_badges,
            },
            'points_timeline': points_timeline,
            'recent_activity': recent_activity,
        })
