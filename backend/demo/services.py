"""Demo pool: seed, lease, reset, tokens.

Lease lock
----------
Each family slot has one cache key ``demo:lease:<slot>``. ``cache.add`` is an
atomic "set if missing" with a TTL (SET NX EX on Redis), so two visitors can
never get the same family, and a lease that is never released simply expires.
The value is ``"<lease_id>:<expires_epoch>"`` so a busy answer can say how long
until the next family frees up.

DEMO_MODE with REDIS_HOST makes Django's default cache Redis (see settings),
which is what makes this lock shared between the gunicorn workers.

Reset
-----
Resetting deletes sessions (cascades to messages, reports, flags, alerts),
AI-made quests, weekly summaries, points, streaks, badges and memory for ONE
child, then seeds the same short synthetic week again. It never calls the
LLM pipeline. Old JWTs of that family are blacklisted, and every demo token
is checked against the live lease on each request (demo/authentication.py),
so a visitor's access ends with their lease.

Account fields a visitor can edit (nickname, icon, language) are restored on
every reset, and demo accounts never get a usable password.
"""
import logging
import random
import secrets
import time
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from authentication.models import (
    ChildProfile,
    ParentChildLink,
    ParentProfile,
)
from authentication.serializers import CustomTokenObtainPairSerializer
from conversation.models import Message, Session, TurnAudit
from gamification.models import (
    ChildBadge,
    ChildQuestProgress,
    ChildStreak,
    Points,
    PointsEvent,
    Quest,
)
from reporting.models import ChildSessionMemory, SessionReport, WeeklySummary
from reporting.services import build_sources_snapshot

from . import content
from .accounts import demo_slot

logger = logging.getLogger(__name__)

User = get_user_model()

CHILD_USERNAME = 'demo-child-{slot}'
PARENT_USERNAME = 'demo-parent-{slot}'
USERNAME_PREFIX = 'demo-'
LEASE_KEY = 'demo:lease:{slot}'
MAINT_LEASE_SECONDS = 60
SEED_LOCK_KEY = 'demo:seed-lock'
SEED_LOCK_SECONDS = 300
SEED_RETRY_SECONDS = 5


class DemoAccountConflict(Exception):
    """A demo username belongs to an account the demo did not make."""


class LeaseLost(Exception):
    """The visitor's lease ended before the reset could start."""


class DemoBusy(Exception):
    """All families are leased."""

    def __init__(self, retry_after):
        super().__init__('all demo families are busy')
        self.retry_after = retry_after


# ----------------------------------------------------------------------
# Text and slots
# ----------------------------------------------------------------------

def render(text, name, age, gender):
    """Fill the placeholders listed in content.py for a boy or a girl."""
    girl = gender == 'female'
    return text.format(
        name=name,
        age=age,
        ta='ة' if girl else '',
        y='ي' if girl else '',
        yn='ين' if girl else '',
        t='ت' if girl else '',
        h='ها' if girl else 'ه',
        p='ت' if girl else 'ي',
    )


def slot_from_username(username):
    """'demo-child-3' or 'demo-parent-3' -> 3, anything else -> None."""
    return demo_slot(username)


def _seeded_slots():
    """Every slot that has its demo accounts, whatever DEMO_POOL_SIZE says."""
    names = User.objects.filter(
        username__startswith='demo-child-', is_child=True
    ).values_list('username', flat=True)
    return {s for s in (slot_from_username(n) for n in names) if s}


def pool_slots():
    """Seeded slots, never more than DEMO_POOL_SIZE or the families we have."""
    limit = min(settings.DEMO_POOL_SIZE, len(content.FAMILIES))
    return sorted(s for s in _seeded_slots() if s <= limit)


def get_family(slot):
    child = ChildProfile.objects.select_related('user').get(
        user__username=CHILD_USERNAME.format(slot=slot)
    )
    parent = ParentProfile.objects.select_related('user').get(
        user__username=PARENT_USERNAME.format(slot=slot)
    )
    return parent, child


# ----------------------------------------------------------------------
# Seeding and reset
# ----------------------------------------------------------------------

def _ensure_quests(lang='ar'):
    from session_moral_context.models import Value

    values = dict(Value.objects.values_list('slug', 'pk'))
    quests = {}
    for key, title, description, points, qtype, verification in (
        content.QUESTS_EN if lang == 'en' else content.QUESTS
    ):
        quest, _ = Quest.objects.get_or_create(
            title=title,
            is_ai_generated=False,
            defaults={
                'description': description,
                'reward_points': points,
                'quest_type': qtype,
                'verification_method': verification,
            },
        )
        want = values.get(content.QUEST_VALUES.get(key))
        if want and quest.value_id is None:
            Quest.objects.filter(pk=quest.pk).update(value_id=want)
            quest.value_id = want
        quests[key] = quest
    return quests


def _demo_user(username, role, fields):
    """Get or create one demo user and put its fields back as seeded.

    Refuses to adopt an account the demo did not make (a usable password or
    the wrong role), so seeding can never take over a real person's account.
    """
    user, created = User.objects.get_or_create(
        username=username, defaults={**fields, role: True}
    )
    if not created and (user.has_usable_password() or not getattr(user, role)):
        raise DemoAccountConflict(
            f'{username} exists and is not a demo account; refusing to take it over.'
        )
    for key, value in fields.items():
        setattr(user, key, value)
    user.is_active = True
    user.set_unusable_password()
    user.save()
    return user


def _ensure_accounts(slot):
    """Create (or restore) the parent and child accounts for one slot."""
    _, name, age, gender, icon, pfirst, plast, _theme = content.FAMILIES[slot - 1]
    year = timezone.now().year

    parent_user = _demo_user(
        PARENT_USERNAME.format(slot=slot),
        'is_parent',
        {
            'email': content.PARENT_EMAIL.format(slot=slot),
            'first_name': pfirst,
            'last_name': plast,
        },
    )
    parent, _ = ParentProfile.objects.update_or_create(
        user=parent_user,
        defaults={'name': f'{pfirst} {plast}', 'phone': '', 'birth_year': None},
    )

    child_user = _demo_user(
        CHILD_USERNAME.format(slot=slot),
        'is_child',
        {'email': '', 'first_name': name, 'last_name': ''},
    )
    child, _ = ChildProfile.objects.update_or_create(
        user=child_user,
        defaults={
            'nickname': name,
            'gender': gender,
            'birth_year': year - age,
            'language_preference': 'ar',
            'profile_icon': icon,
            'avatar_visible': True,
        },
    )
    # One demo parent, one demo child, nobody else.
    ParentChildLink.objects.filter(parent=parent).exclude(child=child).delete()
    ParentChildLink.objects.filter(child=child).exclude(parent=parent).delete()
    link, _ = ParentChildLink.objects.update_or_create(
        parent=parent, child=child, defaults={'consent_status': 'approved'}
    )
    return parent, child, link


def _wipe_child(child):
    """Delete everything a visitor (or an earlier reset) left for this child."""
    Quest.objects.filter(
        session_report__session__child=child, is_ai_generated=True
    ).delete()
    ChildQuestProgress.objects.filter(child=child).delete()
    PointsEvent.objects.filter(child=child).delete()
    ChildBadge.objects.filter(child=child).delete()
    WeeklySummary.objects.filter(child=child).delete()
    Session.objects.filter(child=child).delete()
    ChildSessionMemory.objects.filter(child=child).delete()
    Points.objects.filter(child=child).delete()
    ChildStreak.objects.filter(child=child).delete()


def _seed_history(slot, parent, child, link):
    _, name, age, gender, _icon, _pf, _pl, theme_idx = content.FAMILIES[slot - 1]
    seed_week(parent, child, link, name=name, age=age, gender=gender,
              theme=content.THEMES[theme_idx], room_prefix=f'demo-{slot}', rotate=slot)


def seed_week(parent, child, link, *, name, age, gender, theme, room_prefix, rotate, lang='ar'):
    """Seed one synthetic week for a wiped child: sessions, reports, sources,
    weekly summary, quests, points, streak and memory. ``lang`` picks the quest
    set and the words written outside the theme; ``rotate`` varies the sources."""
    now = timezone.now()
    quests = _ensure_quests(lang)
    words = content.SEED_TEXT[lang]

    sessions = theme['sessions']
    n = len(sessions)
    base = (theme['points'] - 10) // n
    extra = (theme['points'] - 10) - base * n

    reports = []
    for i, spec in enumerate(sessions):
        start = (now - timedelta(days=spec['days_ago'])).replace(
            hour=16 + (i % 3), minute=10, second=0, microsecond=0
        )
        if i == n - 1:  # the parent page is "this week": never let this one fall into last week
            week_start = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
            first = timezone.make_aware(
                datetime.combine(week_start, datetime.min.time())) + timedelta(minutes=10)
            start = max(start, first)
        end = start + timedelta(minutes=spec['minutes'])
        session = Session.objects.create(
            child=child,
            livekit_room_name=f'{room_prefix}-{secrets.token_hex(4)}-{i}',
            status='ended',
            mood_state=spec['mood'],
            ended_at=end,
        )
        Session.objects.filter(pk=session.pk).update(started_at=start, ended_at=end)

        step = max(1, int(spec['minutes'] * 60 / (len(spec['messages']) + 1)))
        for j, (sender, text) in enumerate(spec['messages']):
            msg = Message.objects.create(
                session=session,
                sender=sender,
                content=render(text, name, age, gender),
                input_type='voice',
                language=lang,
            )
            Message.objects.filter(pk=msg.pk).update(
                created_at=start + timedelta(seconds=step * (j + 1))
            )

        report = SessionReport.objects.create(
            session=session,
            insight_summary=render(spec['insight'], name, age, gender),
            recommendations=render(spec['recommendations'], name, age, gender),
            raw_llm_output={'demo': True, 'values_to_revisit': spec['values_to_revisit']},
        )
        SessionReport.objects.filter(pk=report.pk).update(created_at=end)
        reports.append(report)

        delta = base + (extra if i == n - 1 else 0)
        event = PointsEvent.objects.create(
            child=child,
            delta=delta,
            reason=words['session_reason'],
            source='conversation',
            session=session,
        )
        PointsEvent.objects.filter(pk=event.pk).update(created_at=end)

    _seed_sources(rotate, child, reports[-1].session)

    # Weekly summary for the parent dashboard.
    oldest = (now - timedelta(days=sessions[0]['days_ago'])).date()
    week_start = oldest - timedelta(days=oldest.weekday())
    weekly = WeeklySummary.objects.create(
        child=child,
        parent=parent,
        week_start=week_start,
        summary=render(theme['summary'], name, age, gender),
        suggested_topics=[render(t, name, age, gender) for t in theme['topics']],
    )
    weekly.sessions.set(reports)

    # Quests: one done, one waiting for the parent, one under way, one new.
    quest_done = now - timedelta(days=1)
    ChildQuestProgress.objects.create(
        child=child, quest=quests['honest'], status='completed',
        started_at=quest_done - timedelta(hours=20), completed_at=quest_done,
        verified_by='child',
    )
    ChildQuestProgress.objects.create(
        child=child, quest=quests['help'], status='pending_verification',
        started_at=now - timedelta(hours=18),
        proof_note=words['proof_note'],
    )
    ChildQuestProgress.objects.create(
        child=child, quest=quests['share'], status='in_progress',
        started_at=now - timedelta(hours=5),
    )
    ChildQuestProgress.objects.create(
        child=child, quest=quests['ask'], status='not_started',
    )
    quest_event = PointsEvent.objects.create(
        child=child, delta=10, reason=quests['honest'].title, source='quest'
    )
    PointsEvent.objects.filter(pk=quest_event.pk).update(created_at=quest_done)

    Points.objects.create(child=child, total=theme['points'])
    last = now - timedelta(days=sessions[-1]['days_ago'])
    ChildStreak.objects.create(
        child=child, current_streak=1, longest_streak=2,
        last_active_date=timezone.localtime(last).date(),
    )

    memory = render(theme['memory'], name, age, gender)
    ChildSessionMemory.objects.create(child=child, rolling_summary=memory)
    ParentChildLink.objects.filter(pk=link.pk).update(memory=memory)


def _seed_sources(slot, child, session):
    """Reference rows (never text) for the parent's "Sources discussed" page.

    Picks reviewed or servable bank items (hadith with English text first, then
    verses, then one other type), rotated by slot so families differ, and
    stamps them today and earlier this week. Skips quietly if the bank is empty.
    """
    from session_moral_context.models import ContentItem, ServedReference

    pool = ContentItem.objects.servable().order_by('pk')
    groups = [
        (list(pool.filter(type='hadith').exclude(english_text='')), 2),
        (list(pool.filter(type='verse')), 2),
        (list(pool.exclude(type__in=['hadith', 'verse'])), 1),
    ]
    picks = []
    for items, take in groups:
        picks += [items[(slot + k) % len(items)] for k in range(min(take, len(items)))]
    if not picks:
        logger.warning('demo: knowledge bank not seeded (run seed_content); no sources for slot %s', slot)
        return
    now = timezone.now()
    today = timezone.localdate()
    days = [0] if today.weekday() == 0 else [0, 1]
    for k, item in enumerate(picks):
        ref = ServedReference.objects.create(
            session=session, item=item, via='inject' if k % 2 == 0 else 'tool')
        ServedReference.objects.filter(pk=ref.pk).update(
            served_at=now - timedelta(days=days[k % len(days)]))
    TurnAudit.objects.create(
        session=session, level='D', mode='REFER', served_item_ids=[picks[0].pk])
    SessionReport.objects.filter(session=session).update(
        sources_used=build_sources_snapshot(session))


def _topup_sources(slot):
    """Give an already-seeded family sources if it has none (older seeds)."""
    from session_moral_context.models import ServedReference

    _, child = get_family(slot)
    if ServedReference.objects.filter(session__child=child).exists():
        return
    session = Session.objects.filter(
        child=child, status='ended', livekit_room_name__startswith=f'demo-{slot}-'
    ).order_by('-started_at').first()
    if session is None:
        return
    first = timezone.make_aware(datetime.combine(
        timezone.localdate() - timedelta(days=timezone.localdate().weekday()),
        datetime.min.time())) + timedelta(minutes=10)
    if session.started_at < first:
        Session.objects.filter(pk=session.pk).update(
            started_at=first, ended_at=first + timedelta(minutes=5))
        session.refresh_from_db()
    _seed_sources(slot, child, session)


@transaction.atomic
def reset_family(slot):
    """Wipe and re-seed one family. Returns (parent, child)."""
    parent, child, link = _ensure_accounts(slot)
    _wipe_child(child)
    ChildProfile.objects.filter(pk=child.pk).update(last_seen_at=None)
    _seed_history(slot, parent, child, link)
    _blacklist_tokens([parent.user, child.user])
    return parent, child


def _blacklist_tokens(users):
    """Invalidate every refresh token ever issued to these users."""
    done = BlacklistedToken.objects.values('token_id')
    pending = OutstandingToken.objects.filter(user__in=users).exclude(
        id__in=done
    )
    BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=t) for t in pending], ignore_conflicts=True
    )


def seed_pool(size=None):
    """Create the whole pool (idempotent). Each run also resets each family."""
    size = size or settings.DEMO_POOL_SIZE
    slots = []
    for slot in range(1, min(size, len(content.FAMILIES)) + 1):
        reset_family(slot)
        slots.append(slot)
    return slots


def ensure_pool(size=None):
    """Seed only the families that do not exist yet. Safe on a live pool.

    ``seed_pool`` wipes every family it touches, which would pull the rug from
    under a visitor who holds a lease. This one only adds missing sources to an unleased seeded family, so
    it can run on every deploy (``seed_demo --ensure``) and again from the first
    visitor on a fresh database. A short cache lock keeps two processes from
    seeding the same slot at once. Returns the slots it created, or None when
    another process holds the lock.
    """
    size = min(size or settings.DEMO_POOL_SIZE, len(content.FAMILIES))
    if not cache.add(SEED_LOCK_KEY, '1', SEED_LOCK_SECONDS):
        return None
    try:
        have = _seeded_slots()
        created = []
        for slot in range(1, size + 1):
            if slot not in have:
                reset_family(slot)
                created.append(slot)
            elif not cache.get(LEASE_KEY.format(slot=slot)):
                try:
                    _topup_sources(slot)
                except Exception:
                    logger.exception('demo topup failed for slot %s', slot)
        return created
    finally:
        cache.delete(SEED_LOCK_KEY)


# ----------------------------------------------------------------------
# Lease
# ----------------------------------------------------------------------

def _lease_value(lease_id, seconds):
    return f'{lease_id}:{int(time.time()) + seconds}'


def _parse_lease(value):
    """-> (lease_id, expires_epoch) or (None, 0)."""
    if not value or ':' not in str(value):
        return None, 0
    lease_id, _, exp = str(value).partition(':')
    try:
        return lease_id, int(exp)
    except ValueError:
        return lease_id, 0


def lease_holder_matches(slot, lease_id):
    held, _ = _parse_lease(cache.get(LEASE_KEY.format(slot=slot)))
    return bool(lease_id) and held == lease_id


def extend_lease(slot, lease_id):
    cache.set(
        LEASE_KEY.format(slot=slot),
        _lease_value(lease_id, settings.DEMO_LEASE_SECONDS),
        settings.DEMO_LEASE_SECONDS,
    )


def acquire_slot():
    """Take any free family. Returns (slot, lease_id) or raises DemoBusy."""
    slots = pool_slots()
    if not slots:
        # A fresh database: seed the pool now instead of answering 503 until
        # someone runs seed_demo by hand. Whoever loses the lock waits a moment.
        ensure_pool()
        slots = pool_slots()
        if not slots:
            raise DemoBusy(retry_after=SEED_RETRY_SECONDS)
    random.shuffle(slots)
    lease_id = secrets.token_hex(8)
    for slot in slots:
        ok = cache.add(
            LEASE_KEY.format(slot=slot),
            _lease_value(lease_id, settings.DEMO_LEASE_SECONDS),
            settings.DEMO_LEASE_SECONDS,
        )
        if ok:
            return slot, lease_id
    soonest = None
    for slot in slots:
        _, exp = _parse_lease(cache.get(LEASE_KEY.format(slot=slot)))
        if exp:
            soonest = exp if soonest is None else min(soonest, exp)
    wait = max(30, (soonest or 0) - int(time.time())) if soonest else 60
    raise DemoBusy(retry_after=min(wait, settings.DEMO_LEASE_SECONDS))


def release_slot(slot, lease_id):
    key = LEASE_KEY.format(slot=slot)
    held, _ = _parse_lease(cache.get(key))
    if held == lease_id:
        cache.delete(key)


def start_demo():
    """Lease a family, reset it, and return a payload for the browser."""
    slot, lease_id = acquire_slot()
    try:
        parent, child = reset_family(slot)
    except Exception:
        release_slot(slot, lease_id)
        logger.exception('demo reset failed for slot %s', slot)
        raise
    return build_payload(slot, lease_id, parent, child)


def restart_demo(slot, lease_id):
    """Start over inside the visitor's own family (lease must still be theirs).

    The lease is renewed before the wipe, not after it, so it cannot lapse
    (and pass to a new visitor) while the reset runs.
    """
    if not lease_holder_matches(slot, lease_id):
        raise LeaseLost()
    extend_lease(slot, lease_id)
    parent, child = reset_family(slot)
    return build_payload(slot, lease_id, parent, child)


def reset_expired():
    """Reset every family whose lease has run out. Returns the slots reset.

    A short maintenance lease keeps a new visitor from being handed a
    family that is being wiped at this very moment.
    """
    reset = []
    for slot in pool_slots():
        key = LEASE_KEY.format(slot=slot)
        marker = f'maint-{secrets.token_hex(4)}'
        if not cache.add(
            key, _lease_value(marker, MAINT_LEASE_SECONDS), MAINT_LEASE_SECONDS
        ):
            continue  # leased by a visitor
        try:
            reset_family(slot)
            reset.append(slot)
        finally:
            release_slot(slot, marker)
    return reset


# ----------------------------------------------------------------------
# Tokens
# ----------------------------------------------------------------------

def _tokens_for(user, slot, lease_id):
    refresh = CustomTokenObtainPairSerializer.get_token(user)
    refresh['demo_lease'] = lease_id
    refresh['demo_slot'] = slot
    lifetime = timedelta(seconds=settings.DEMO_LEASE_SECONDS)
    refresh.set_exp(lifetime=lifetime)
    access = refresh.access_token
    # Never outlive the lease: an access token lasts at most as long as it.
    access.set_exp(
        lifetime=min(lifetime, settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'])
    )
    return {
        'access': str(access),
        'refresh': str(refresh),
        'user_id': user.id,
        'username': user.username,
        'is_parent': user.is_parent,
        'is_child': user.is_child,
    }


def build_payload(slot, lease_id, parent, child):
    return {
        'child': _tokens_for(child.user, slot, lease_id),
        'parent': _tokens_for(parent.user, slot, lease_id),
        'family': {
            'slot': slot,
            'child_id': child.id,
            'child_name': child.nickname,
            'child_gender': child.gender,
            'parent_name': parent.name,
        },
        'expires_in': settings.DEMO_LEASE_SECONDS,
    }
