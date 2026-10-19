"""Central gamification engine: points, streaks, badges, quest completion.

Every point change in the app flows through ``award_points`` so the
PointsEvent ledger stays complete and level/badge changes are computed
in one place. Used by:
- conversation agent tools (real-time engagement points, conversation quests)
- gamification views (child quest completion, parent verification)
- conversation.services.start_session (daily streaks)
- reporting pipeline (badge re-check after a session report)
"""
from __future__ import annotations

import logging
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import (
    Badge,
    ChildBadge,
    ChildQuestProgress,
    ChildStreak,
    Level,
    Points,
    PointsEvent,
)

logger = logging.getLogger(__name__)

# Real-time engagement deltas used by the conversation agent.
ENGAGEMENT_DELTAS = {
    'excellent': 10,   # deep moral reflection, honesty moment, learned something
    'good': 5,         # positive engagement with values topics
    'poor': -3,        # drifting to unsuitable topics after a redirect
    'bad': -8,         # persisting with inappropriate topics
}

STREAK_DAILY_BONUS = 5


def _level_snapshot(total: int) -> dict[str, Any]:
    """Level info for a points total (same shape the LevelView exposes)."""
    current = (
        Level.objects.filter(required_points__lte=total)
        .order_by('-required_points')
        .first()
    )
    nxt = (
        Level.objects.filter(required_points__gt=total)
        .order_by('required_points')
        .first()
    )
    if current:
        level_name = current.name
        level_number = current.number
        current_min = current.required_points
    else:
        first = Level.objects.order_by('number').first()
        level_name = first.name if first else 'Beginner'
        level_number = first.number if first else 1
        current_min = 0

    next_min = nxt.required_points if nxt else None
    if next_min is not None and next_min > current_min:
        progress_pct = int((total - current_min) / (next_min - current_min) * 100)
    else:
        progress_pct = 100 if total >= current_min and current_min > 0 else 0

    return {
        'level_name': level_name,
        'level_number': level_number,
        'total_points': total,
        'current_level_min': current_min,
        'next_level_min': next_min,
        'progress_pct': max(0, min(100, progress_pct)),
    }


def award_points(
    child,
    delta: int,
    *,
    reason: str = '',
    source: str = 'adjustment',
    session=None,
) -> dict[str, Any]:
    """Apply a point change atomically and return the resulting level state.

    Negative deltas never push the total below zero (delta_applied reflects
    what actually landed). Returns level snapshot plus ``leveled_up`` /
    ``leveled_down`` so callers can announce changes in real time.
    """
    delta = int(delta)
    with transaction.atomic():
        pts, _ = Points.objects.select_for_update().get_or_create(child=child)
        old_total = pts.total
        new_total = max(0, old_total + delta)
        applied = new_total - old_total
        pts.total = new_total
        pts.save(update_fields=['total'])
        if applied != 0:
            PointsEvent.objects.create(
                child=child,
                delta=applied,
                reason=reason[:255],
                source=source,
                session=session,
            )

    before = _level_snapshot(old_total)
    after = _level_snapshot(new_total)
    after['delta_applied'] = applied
    after['leveled_up'] = after['level_number'] > before['level_number']
    after['leveled_down'] = after['level_number'] < before['level_number']
    return after


def update_streak(child, *, today=None) -> dict[str, Any]:
    """Roll the child's daily streak forward; call when a session starts.

    Returns streak state plus ``extended`` (True when today added a new day).
    Awards a small daily bonus through award_points when the streak extends.
    """
    today = today or timezone.localdate()
    with transaction.atomic():
        streak, _ = ChildStreak.objects.select_for_update().get_or_create(child=child)
        extended = False
        if streak.last_active_date == today:
            pass  # already counted today
        elif streak.last_active_date == today - timezone.timedelta(days=1):
            streak.current_streak += 1
            extended = True
        else:
            # First session ever, or the chain broke — today starts a new one.
            streak.current_streak = 1
            extended = True
        streak.last_active_date = today
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        streak.save()

    if extended:
        award_points(
            child,
            STREAK_DAILY_BONUS,
            reason=f'Daily streak: day {streak.current_streak}',
            source='streak',
        )

    return {
        'current_streak': streak.current_streak,
        'longest_streak': streak.longest_streak,
        'extended': extended,
    }


def _child_stat(child, requirement_type: str) -> int:
    """Current value of the stat a badge requirement checks against."""
    if requirement_type == 'streak_days':
        streak = ChildStreak.objects.filter(child=child).first()
        return streak.longest_streak if streak else 0
    if requirement_type == 'quests_completed':
        return ChildQuestProgress.objects.filter(
            child=child, status='completed'
        ).count()
    if requirement_type == 'level_reached':
        pts = Points.objects.filter(child=child).first()
        snapshot = _level_snapshot(pts.total if pts else 0)
        return snapshot['level_number']
    if requirement_type == 'values_practised':
        # Distinct bank Values across completed quests. Counts concrete deeds,
        # never a score: the child is not graded on any value (decision 5 Oct).
        return (
            ChildQuestProgress.objects.filter(
                child=child, status='completed', quest__value__isnull=False
            )
            .values('quest__value')
            .distinct()
            .count()
        )
    if requirement_type == 'sessions_count':
        from conversation.models import Session
        return Session.objects.filter(child=child, status='ended').count()
    if requirement_type == 'points_total':
        pts = Points.objects.filter(child=child).first()
        return pts.total if pts else 0
    return 0


def evaluate_badges(child) -> list[Badge]:
    """Award any auto-awardable badges the child now qualifies for.

    Returns the list of newly earned Badge objects (empty when none).
    """
    earned_ids = set(
        ChildBadge.objects.filter(child=child).values_list('badge_id', flat=True)
    )
    candidates = Badge.objects.exclude(requirement_type='manual').exclude(
        id__in=earned_ids
    )

    # Compute each stat at most once per call.
    stats: dict[str, int] = {}
    newly_earned: list[Badge] = []
    for badge in candidates:
        rt = badge.requirement_type
        if rt not in stats:
            stats[rt] = _child_stat(child, rt)
        if badge.requirement_value > 0 and stats[rt] >= badge.requirement_value:
            _, created = ChildBadge.objects.get_or_create(child=child, badge=badge)
            if created:
                newly_earned.append(badge)
                logger.info(
                    'Badge awarded: child_id=%s badge=%s', child.id, badge.name
                )
    return newly_earned


def complete_quest_progress(
    progress: ChildQuestProgress,
    *,
    verified_by: str,
    session=None,
) -> dict[str, Any]:
    """Mark a quest progress row completed, award its points, check badges.

    Single completion path used by the child API, the companion agent and
    the parent verification flow. Returns::

        {'progress', 'points', 'new_badges'}

    ``points`` is None (and no badges) when another caller already completed it.
    """
    now = timezone.now()
    # Claim the row atomically: of several concurrent callers (double tap, two parents,
    # child + companion) only the one that flips it to completed gets paid.
    claim = ChildQuestProgress.objects.filter(pk=progress.pk).exclude(status='completed')
    if verified_by == 'parent':
        # A parent approves only what is still awaiting verification; a concurrent reject wins.
        claim = claim.filter(status='pending_verification')
    claimed = (
        claim
        .update(
            status='completed',
            completed_at=now,
            verified_by=verified_by,
            started_at=progress.started_at or now,
        )
    )
    if not claimed:
        progress.refresh_from_db()
        return {'progress': progress, 'points': None, 'new_badges': []}
    progress.refresh_from_db()

    points = award_points(
        progress.child,
        progress.quest.reward_points,
        reason=f'Quest completed: {progress.quest.title}',
        source='quest',
        session=session,
    )
    new_badges = evaluate_badges(progress.child)
    return {'progress': progress, 'points': points, 'new_badges': new_badges}


def gamification_state(child) -> dict[str, Any]:
    """Compact snapshot for the agent / live UI: level + streak."""
    pts = Points.objects.filter(child=child).first()
    snapshot = _level_snapshot(pts.total if pts else 0)
    streak = ChildStreak.objects.filter(child=child).first()
    snapshot['current_streak'] = streak.current_streak if streak else 0
    return snapshot
