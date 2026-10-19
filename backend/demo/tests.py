"""Tests for the one-click demo pool (sqlite settings, LocMem cache)."""
import re
from datetime import timedelta
from io import StringIO

from django.conf import settings
from django.core.cache import cache, caches
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from authentication.models import ChildProfile, ParentChildLink
from conversation.models import Message, Session
from gamification.models import ChildQuestProgress, Points, Quest
from reporting.models import ChildSessionMemory, SessionReport, WeeklySummary

from . import content, services

START = '/api/demo/start'
RESET = '/api/demo/reset'


TEST_CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    'throttle': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'demo-throttle'},
}


def bearer(token):
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@override_settings(
    DEMO_MODE=True,
    DEMO_POOL_SIZE=8,
    DEMO_LEASE_SECONDS=600,
    CACHES=TEST_CACHES,
)
class DemoBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', stdout=StringIO())

    def setUp(self):
        cache.clear()
        caches['throttle'].clear()
        self.client = APIClient()


class SeedTests(DemoBase):
    def test_pool_has_eight_synthetic_families(self):
        self.assertEqual(services.pool_slots(), list(range(1, 9)))
        self.assertEqual(ChildProfile.objects.count(), 8)
        for child in ChildProfile.objects.all():
            self.assertTrue(6 <= (timezone_year() - child.birth_year) <= 13)
            self.assertEqual(child.language_preference, 'ar')
            self.assertTrue(child.parents.filter(consent_status='approved').exists())
            self.assertFalse(child.user.has_usable_password())

    def test_each_family_has_a_week_of_history(self):
        for child in ChildProfile.objects.all():
            self.assertEqual(child.sessions.count(), 3)
            self.assertEqual(Message.objects.filter(session__child=child).count(), 12)
            self.assertEqual(SessionReport.objects.filter(session__child=child).count(), 3)
            self.assertEqual(WeeklySummary.objects.filter(child=child).count(), 1)
            self.assertTrue(ChildSessionMemory.objects.filter(child=child).exists())
            self.assertGreater(Points.objects.get(child=child).total, 0)
            self.assertEqual(ChildQuestProgress.objects.filter(child=child).count(), 4)

    def test_history_is_backdated(self):
        first = Session.objects.filter(child__user__username='demo-child-1').order_by('started_at').first()
        self.assertGreater(
            first.ended_at - first.started_at, timedelta(minutes=1)
        )
        from django.utils import timezone
        self.assertLess(first.started_at, timezone.now() - timedelta(days=4))

    def test_seed_is_idempotent(self):
        call_command('seed_demo', stdout=StringIO())
        self.assertEqual(ChildProfile.objects.count(), 8)
        self.assertEqual(Session.objects.count(), 24)
        self.assertEqual(Quest.objects.filter(is_ai_generated=False).count(), len(content.QUESTS))

    def test_no_scripture_in_content(self):
        # Quran brackets and Quranic annotation marks never appear in the demo text. Real sources come from the content bank only.
        blob = repr(content.THEMES) + repr(content.QUESTS)
        self.assertIsNone(re.search('[ۖ-ۭ﴾﴿۝]', blob))
        for banned in ('قال رسول الله', 'قال الله تعالى', 'بسم الله الرحمن'):
            self.assertNotIn(banned, blob)


def timezone_year():
    from django.utils import timezone
    return timezone.now().year


class DisabledTests(TestCase):
    @override_settings(DEMO_MODE=False)
    def test_start_is_404_when_off(self):
        self.assertEqual(APIClient().post(START).status_code, 404)

    @override_settings(DEMO_MODE=False)
    def test_reset_is_404_when_off(self):
        self.assertEqual(APIClient().post(RESET).status_code, 404)


class StartTests(DemoBase):
    def test_start_returns_working_tokens(self):
        resp = self.client.post(START)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data['child']['is_child'])
        self.assertTrue(data['parent']['is_parent'])
        self.assertIn('access', data['child'])
        self.assertIn('refresh', data['parent'])

        me = self.client.get('/api/auth/profile/', **bearer(data['child']['access']))
        self.assertEqual(me.status_code, 200)

        kids = self.client.get('/api/auth/children/', **bearer(data['parent']['access']))
        self.assertEqual(kids.status_code, 200)
        body = kids.json()
        rows = body['results'] if isinstance(body, dict) and 'results' in body else body
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['id'], data['family']['child_id'])

    def test_refresh_token_works(self):
        data = self.client.post(START).json()
        resp = self.client.post('/api/auth/token/refresh/', {'refresh': data['child']['refresh']}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.json())

    def test_stale_token_does_not_break_start(self):
        resp = self.client.post(START, **bearer('not-a-real-token'))
        self.assertEqual(resp.status_code, 201)

    def test_two_visitors_get_different_families(self):
        a = self.client.post(START).json()['family']['slot']
        b = self.client.post(START).json()['family']['slot']
        self.assertNotEqual(a, b)

    def test_busy_when_all_leased(self):
        for _ in range(8):
            self.assertEqual(self.client.post(START).status_code, 201)
        resp = self.client.post(START)
        self.assertEqual(resp.status_code, 503)
        body = resp.json()
        self.assertEqual(body['code'], 'demo_busy')
        self.assertTrue(body['message_ar'])
        self.assertTrue(body['message_en'])
        self.assertIn('Retry-After', resp)

    def test_expired_lease_frees_the_family(self):
        for _ in range(8):
            self.client.post(START)
        cache.delete(services.LEASE_KEY.format(slot=3))
        resp = self.client.post(START)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()['family']['slot'], 3)

    def test_new_lease_wipes_the_previous_visitors_data(self):
        first = self.client.post(START).json()
        slot = first['family']['slot']
        child = ChildProfile.objects.get(pk=first['family']['child_id'])
        Session.objects.create(child=child, livekit_room_name='visitor-room', status='ended')
        Points.objects.filter(child=child).update(total=999)
        # Lease every other family, then free this one: it is the only choice.
        for _ in range(7):
            self.client.post(START)
        cache.delete(services.LEASE_KEY.format(slot=slot))
        second = self.client.post(START).json()
        self.assertEqual(second['family']['slot'], slot)
        self.assertFalse(Session.objects.filter(livekit_room_name='visitor-room').exists())
        self.assertNotEqual(Points.objects.get(child=child).total, 999)
        # Old visitor's refresh token no longer works.
        old = self.client.post('/api/auth/token/refresh/', {'refresh': first['child']['refresh']}, format='json')
        self.assertEqual(old.status_code, 401)
        self.assertTrue(BlacklistedToken.objects.exists())

    def test_start_is_throttled_per_ip(self):
        from unittest import mock
        from rest_framework.throttling import ScopedRateThrottle
        with mock.patch.dict(ScopedRateThrottle.THROTTLE_RATES, {'demo_start': '3/hour'}):
            codes = [self.client.post(START, REMOTE_ADDR='9.9.9.9').status_code for _ in range(4)]
            other = self.client.post(START, REMOTE_ADDR='8.8.8.8').status_code
        self.assertEqual(codes, [201, 201, 201, 429])
        self.assertEqual(other, 201)

    def test_default_start_rate_fits_a_room_of_judges_behind_one_nat(self):
        # About 30 judges share one IP and the busy page retries by itself, so the old
        # 10/hour locked the room out. Skipped when the environment overrides the rate.
        import os
        from rest_framework.throttling import ScopedRateThrottle
        if os.getenv('DEMO_START_RATE') or os.getenv('DEMO_RESET_RATE'):
            self.skipTest('rate overridden by the environment')
        for scope in ('demo_start', 'demo_reset'):
            count, _, period = ScopedRateThrottle.THROTTLE_RATES[scope].partition('/')
            self.assertEqual(period, 'hour')
            self.assertGreaterEqual(int(count), 100)


class ResetTests(DemoBase):
    def test_start_over_wipes_and_reseeds(self):
        data = self.client.post(START).json()
        child = ChildProfile.objects.get(pk=data['family']['child_id'])
        Session.objects.create(child=child, livekit_room_name='mine', status='ended')
        ChildSessionMemory.objects.filter(child=child).update(rolling_summary='visitor wrote this')

        resp = self.client.post(RESET, **bearer(data['child']['access']))
        self.assertEqual(resp.status_code, 201)
        again = resp.json()
        self.assertEqual(again['family']['slot'], data['family']['slot'])
        self.assertFalse(Session.objects.filter(livekit_room_name='mine').exists())
        self.assertEqual(child.sessions.count(), 3)
        self.assertNotIn('visitor wrote this', ChildSessionMemory.objects.get(child=child).rolling_summary)

        # The fresh tokens work, the old refresh token does not.
        ok = self.client.get('/api/auth/profile/', **bearer(again['parent']['access']))
        self.assertEqual(ok.status_code, 200)
        old = self.client.post('/api/auth/token/refresh/', {'refresh': data['child']['refresh']}, format='json')
        self.assertEqual(old.status_code, 401)

    def test_start_over_requires_login(self):
        self.assertEqual(self.client.post(RESET).status_code, 401)

    def test_start_over_after_lease_lost_is_refused(self):
        # The token itself dies with the lease (401); the browser then starts afresh.
        data = self.client.post(START).json()
        cache.delete(services.LEASE_KEY.format(slot=data['family']['slot']))
        resp = self.client.post(RESET, **bearer(data['child']['access']))
        self.assertEqual(resp.status_code, 401)

    def test_restart_raises_when_lease_lapsed(self):
        data = self.client.post(START).json()
        slot = data['family']['slot']
        lease_id = services._parse_lease(cache.get(services.LEASE_KEY.format(slot=slot)))[0]
        cache.delete(services.LEASE_KEY.format(slot=slot))
        with self.assertRaises(services.LeaseLost):
            services.restart_demo(slot, lease_id)

    def test_start_over_by_a_non_demo_user_is_refused(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user('real_parent', password='x-pass-123', is_parent=True)
        from rest_framework_simplejwt.tokens import RefreshToken
        token = str(RefreshToken.for_user(user).access_token)
        self.assertEqual(self.client.post(RESET, **bearer(token)).status_code, 409)

    def test_reset_expired_only_touches_free_families(self):
        data = self.client.post(START).json()
        held = data['family']['slot']
        child = ChildProfile.objects.get(pk=data['family']['child_id'])
        Session.objects.create(child=child, livekit_room_name='keep-me', status='ended')
        free = ChildProfile.objects.exclude(pk=child.pk).first()
        Session.objects.create(child=free, livekit_room_name='wipe-me', status='ended')

        out = StringIO()
        call_command('demo_reset_expired', stdout=out)
        self.assertTrue(Session.objects.filter(livekit_room_name='keep-me').exists())
        self.assertFalse(Session.objects.filter(livekit_room_name='wipe-me').exists())
        self.assertNotIn(held, services.reset_expired())

    def test_reset_expired_leaves_no_lock_behind(self):
        call_command('demo_reset_expired', stdout=StringIO())
        self.assertEqual(self.client.post(START).status_code, 201)


class TokenScopeTests(DemoBase):
    def test_tokens_never_outlive_the_lease(self):
        from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
        data = self.client.post(START).json()
        import time
        horizon = time.time() + settings.DEMO_LEASE_SECONDS + 5
        self.assertLess(AccessToken(data['child']['access'])['exp'], horizon)
        self.assertLess(RefreshToken(data['child']['refresh'])['exp'], horizon)

    def test_parent_dashboard_sees_the_seeded_week(self):
        data = self.client.post(START).json()
        child_id = data['family']['child_id']
        resp = self.client.get(f'/api/reporting/insights/{child_id}/', **bearer(data['parent']['access']))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(ParentChildLink.objects.filter(child_id=child_id, consent_status='approved').exists())


class LeaseGateTests(DemoBase):
    """A demo token only works while its own lease is the family's live lease."""

    def refresh(self, token):
        return self.client.post('/api/auth/token/refresh/', {'refresh': token}, format='json')

    def test_rotated_token_dies_with_the_lease(self):
        data = self.client.post(START).json()
        rotated = self.refresh(data['child']['refresh'])
        self.assertEqual(rotated.status_code, 200)
        fresh = rotated.json()
        self.assertEqual(self.client.get('/api/auth/profile/', **bearer(fresh['access'])).status_code, 200)

        cache.delete(services.LEASE_KEY.format(slot=data['family']['slot']))
        self.assertEqual(self.client.get('/api/auth/profile/', **bearer(fresh['access'])).status_code, 401)
        self.assertEqual(self.refresh(fresh['refresh']).status_code, 401)

    def test_last_visitor_cannot_read_the_next_visitors_family(self):
        first = self.client.post(START).json()
        slot = first['family']['slot']
        old_parent = self.refresh(first['parent']['refresh']).json()['access']
        for _ in range(7):
            self.client.post(START)
        cache.delete(services.LEASE_KEY.format(slot=slot))  # first visitor's time is up
        second = self.client.post(START).json()
        self.assertEqual(second['family']['slot'], slot)

        child_id = second['family']['child_id']
        insights = f'/api/reporting/insights/{child_id}/'
        self.assertEqual(self.client.get(insights, **bearer(old_parent)).status_code, 401)
        self.assertEqual(self.client.get(insights, **bearer(first['parent']['access'])).status_code, 401)
        self.assertEqual(self.client.get(insights, **bearer(second['parent']['access'])).status_code, 200)

    def test_demo_tokens_stop_when_demo_mode_is_off(self):
        data = self.client.post(START).json()
        with self.settings(DEMO_MODE=False):
            resp = self.client.get('/api/auth/profile/', **bearer(data['child']['access']))
        self.assertEqual(resp.status_code, 401)

    def test_demo_account_token_without_a_lease_is_refused(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        self.client.post(START)
        child = ChildProfile.objects.get(user__username='demo-child-1')
        token = str(RefreshToken.for_user(child.user).access_token)
        self.assertEqual(self.client.get('/api/auth/profile/', **bearer(token)).status_code, 401)

    def test_real_users_are_untouched(self):
        from django.contrib.auth import get_user_model
        from rest_framework_simplejwt.tokens import RefreshToken
        user = get_user_model().objects.create_user('real_parent', password='x-pass-123', is_parent=True)
        refresh = RefreshToken.for_user(user)
        self.assertEqual(self.client.get('/api/auth/profile/', **bearer(str(refresh.access_token))).status_code, 200)
        self.assertEqual(self.refresh(str(refresh)).status_code, 200)


class AccountLockTests(DemoBase):
    """Visitors can use the demo family but cannot change the shared accounts."""

    def test_demo_child_cannot_set_a_password(self):
        data = self.client.post(START).json()
        resp = self.client.post(
            '/api/auth/profile/child/password/',
            {'new_password': 'Visitor-pass-12345'},
            format='json',
            **bearer(data['child']['access']),
        )
        self.assertEqual(resp.status_code, 403)
        child = ChildProfile.objects.get(pk=data['family']['child_id'])
        self.assertFalse(child.user.has_usable_password())

    def test_demo_parent_can_list_but_not_add_children(self):
        data = self.client.post(START).json()
        auth = bearer(data['parent']['access'])
        self.assertEqual(self.client.get('/api/auth/children/', **auth).status_code, 200)
        resp = self.client.post(
            '/api/auth/children/',
            {'username': 'visitor_kid', 'password': 'Visitor-pass-12345', 'nickname': 'x',
             'birth_year': timezone_year() - 9, 'gender': 'male'},
            format='json',
            **auth,
        )
        self.assertEqual(resp.status_code, 403)

    def test_reset_restores_what_a_visitor_edited(self):
        data = self.client.post(START).json()
        child = ChildProfile.objects.get(pk=data['family']['child_id'])
        seeded = child.nickname
        ChildProfile.objects.filter(pk=child.pk).update(nickname='visitor name', profile_icon='cat', language_preference='en')
        resp = self.client.post(RESET, **bearer(data['child']['access']))
        self.assertEqual(resp.status_code, 201)
        child.refresh_from_db()
        self.assertEqual(child.nickname, seeded)
        self.assertEqual(child.language_preference, 'ar')

    def test_reset_drops_extra_children_on_the_demo_parent(self):
        from authentication.services import create_child_for_parent
        data = self.client.post(START).json()
        parent = ChildProfile.objects.get(pk=data['family']['child_id']).parents.get().parent
        create_child_for_parent(parent, {
            'username': 'stray_kid', 'password': 'Stray-pass-12345', 'nickname': 'stray',
            'birth_year': timezone_year() - 9, 'gender': 'male',
        })
        self.client.post(RESET, **bearer(data['child']['access']))
        self.assertEqual(ParentChildLink.objects.filter(parent=parent).count(), 1)

    def test_registration_refuses_the_demo_prefix(self):
        resp = self.client.post('/api/auth/register/parent/', {
            'username': 'demo-parent-9', 'password': 'Real-pass-12345', 'email': 'p9@example.com',
            'first_name': 'A', 'last_name': 'B',
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('username', resp.json())

    def test_seed_never_takes_over_a_real_account(self):
        child = ChildProfile.objects.get(user__username='demo-child-2')
        child.user.set_password('Someone-else-123')
        child.user.save()
        with self.assertRaises(services.DemoAccountConflict):
            services.reset_family(2)

    @override_settings(DEMO_POOL_SIZE=500)
    def test_pool_never_goes_past_the_seeded_families(self):
        services.seed_pool(500)
        self.assertEqual(services.pool_slots(), list(range(1, len(content.FAMILIES) + 1)))


class ArabicTextTests(DemoBase):
    def test_girls_week_reads_in_the_feminine(self):
        maryam = ChildProfile.objects.get(user__username='demo-child-2')
        self.assertEqual(maryam.gender, 'female')
        summary = WeeklySummary.objects.get(child=maryam).summary
        self.assertIn('فكرت في طرق لمساعدة والدتها', summary)
        yusuf = ChildProfile.objects.get(user__username='demo-child-1')
        self.assertIn('ثم أخبر والدته بنفسه', WeeklySummary.objects.get(child=yusuf).summary)

    def test_every_placeholder_is_filled(self):
        texts = list(Message.objects.values_list('content', flat=True))
        texts += list(SessionReport.objects.values_list('insight_summary', flat=True))
        texts += list(WeeklySummary.objects.values_list('summary', flat=True))
        texts += list(ChildSessionMemory.objects.values_list('rolling_summary', flat=True))
        for text in texts:
            self.assertNotIn('{', text)
            self.assertNotIn('}', text)


# ----------------------------------------------------------------------
# Judging-day capacity: a pool for about 30 judges and a seed that runs by itself
# ----------------------------------------------------------------------

class FamilyContentTests(TestCase):
    def test_pool_is_big_enough_for_a_judging_day(self):
        self.assertGreaterEqual(len(content.FAMILIES), 40)
        self.assertGreaterEqual(settings.DEMO_POOL_SIZE, 30)

    def test_every_family_is_well_formed_and_unique(self):
        from authentication.models import CHILD_PROFILE_ICON_CHOICES
        icons = {key for key, _ in CHILD_PROFILE_ICON_CHOICES}
        self.assertEqual([f[0] for f in content.FAMILIES], list(range(1, len(content.FAMILIES) + 1)))
        for slot, name, age, gender, icon, pfirst, plast, theme in content.FAMILIES:
            self.assertTrue(6 <= age <= 13, slot)
            self.assertIn(gender, ('male', 'female'))
            self.assertIn(icon, icons)
            self.assertTrue(0 <= theme < len(content.THEMES))
            self.assertTrue(name and pfirst and plast)
        parents = [(f[5], f[6]) for f in content.FAMILIES]
        self.assertEqual(len(set(parents)), len(parents), 'two demo parents share a full name')
        # A child's name may repeat a parent's first name (it does for slot 7), but two
        # children in the pool never share a name, so judges can tell their rooms apart.
        names = [f[1] for f in content.FAMILIES]
        self.assertEqual(len(set(names)), len(names), 'two demo children share a name')

    def test_no_scripture_in_the_added_names(self):
        blob = repr(content.FAMILIES)
        self.assertIsNone(re.search('[ۖ-ۭ﴾﴿۝]', blob))


@override_settings(
    DEMO_MODE=True,
    DEMO_POOL_SIZE=8,
    DEMO_LEASE_SECONDS=600,
    CACHES=TEST_CACHES,
)
class EnsurePoolTests(TestCase):
    def setUp(self):
        cache.clear()
        caches['throttle'].clear()
        self.client = APIClient()

    def test_fresh_database_first_visitor_gets_a_room_not_a_503(self):
        self.assertEqual(services.pool_slots(), [])
        resp = self.client.post(START)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(services.pool_slots(), list(range(1, 9)))

    def test_ensure_seeds_only_what_is_missing(self):
        self.assertEqual(services.ensure_pool(3), [1, 2, 3])
        self.assertEqual(services.ensure_pool(5), [4, 5])
        self.assertEqual(services.ensure_pool(5), [])
        self.assertEqual(ChildProfile.objects.count(), 5)

    def test_ensure_never_touches_a_family_that_is_in_use(self):
        services.ensure_pool(4)
        child = ChildProfile.objects.get(user__username='demo-child-2')
        Session.objects.create(child=child, livekit_room_name='live-visitor-room', status='active')
        Points.objects.filter(child=child).update(total=777)
        services.ensure_pool(8)
        self.assertTrue(Session.objects.filter(livekit_room_name='live-visitor-room').exists())
        self.assertEqual(Points.objects.get(child=child).total, 777)
        # The full seed, by contrast, resets every family.
        services.seed_pool(4)
        self.assertFalse(Session.objects.filter(livekit_room_name='live-visitor-room').exists())

    def test_seed_demo_ensure_command_is_idempotent(self):
        out = StringIO()
        call_command('seed_demo', '--ensure', stdout=out)
        self.assertIn('created 8', out.getvalue())
        call_command('seed_demo', '--ensure', stdout=out)
        self.assertIn('created 0', out.getvalue())
        self.assertEqual(ChildProfile.objects.count(), 8)
        self.assertEqual(Session.objects.count(), 24)

    def test_ensure_grows_the_pool_when_the_size_is_raised(self):
        call_command('seed_demo', '--ensure', stdout=StringIO())
        with override_settings(DEMO_POOL_SIZE=12):
            call_command('seed_demo', '--ensure', stdout=StringIO())
            self.assertEqual(services.pool_slots(), list(range(1, 13)))

    def test_a_second_seeder_waits_instead_of_double_seeding(self):
        cache.add(services.SEED_LOCK_KEY, '1', 60)
        self.assertIsNone(services.ensure_pool())
        self.assertEqual(ChildProfile.objects.count(), 0)
        resp = self.client.post(START)
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()['retry_after'], services.SEED_RETRY_SECONDS)
        out = StringIO()
        call_command('seed_demo', '--ensure', stdout=out)
        self.assertIn('Another process is seeding', out.getvalue())

    def test_the_lock_is_released_after_seeding(self):
        services.ensure_pool(2)
        self.assertIsNone(cache.get(services.SEED_LOCK_KEY))


@override_settings(
    DEMO_MODE=True,
    DEMO_POOL_SIZE=40,
    DEMO_LEASE_SECONDS=600,
    CACHES=TEST_CACHES,
)
class JudgingDayTests(TestCase):
    def test_thirty_judges_behind_one_ip_each_get_their_own_family(self):
        cache.clear()
        caches['throttle'].clear()
        client = APIClient()
        slots = []
        for _ in range(30):
            resp = client.post(START, REMOTE_ADDR='203.0.113.7')
            self.assertEqual(resp.status_code, 201)
            slots.append(resp.json()['family']['slot'])
        self.assertEqual(len(set(slots)), 30)
        # Ten more still fit, and only then is the pool full.
        for _ in range(10):
            self.assertEqual(client.post(START, REMOTE_ADDR='203.0.113.7').status_code, 201)
        self.assertEqual(client.post(START, REMOTE_ADDR='203.0.113.7').status_code, 503)


class DeployWiringTests(TestCase):
    """The prod image seeds the demo pool by itself (no hand-run seed_demo after a deploy)."""

    BACKEND = settings.BASE_DIR

    def _read(self, *parts):
        import os
        with open(os.path.join(self.BACKEND, *parts), 'rb') as handle:
            return handle.read()

    def test_dockerfile_starts_the_entrypoint(self):
        self.assertIn(b'docker-entrypoint.sh', self._read('Dockerfile'))

    def test_entrypoint_seeds_idempotently_after_migrations_and_never_migrates(self):
        raw = self._read('docker-entrypoint.sh')
        self.assertNotIn(b'\r', raw, 'the entrypoint must use LF line endings')
        text = raw.decode('utf-8')
        self.assertIn('DEMO_MODE', text)
        self.assertIn('manage.py seed_demo --ensure', text)
        self.assertIn('manage.py migrate --check', text)
        for line in text.splitlines():
            code = line.strip()
            if code.startswith('#'):
                continue
            self.assertNotRegex(code, r'manage\.py migrate(?! --check)')
            self.assertNotRegex(code, r'manage\.py seed_demo(?! --ensure)')
        # gunicorn takes over the process, so the container stops when it stops.
        self.assertRegex(text, r'(?m)^exec gunicorn ')


@override_settings(
    DEMO_MODE=True,
    DEMO_POOL_SIZE=3,
    CACHES=TEST_CACHES,
)
class DemoSourcesTests(TestCase):
    """Parent "Sources discussed this week" has data for every demo family."""

    def setUp(self):
        cache.clear()
        caches['throttle'].clear()
        call_command('seed_content', stdout=StringIO())

    def insights(self, slot=1):
        parent, child = services.get_family(slot)
        c = APIClient()
        c.force_authenticate(parent.user)
        return c.get(f'/api/reporting/insights/{child.id}/').json()

    def check(self):
        for slot in (1, 2, 3):
            data = self.insights(slot)
            self.assertGreaterEqual(len(data['sources']), 4)
            self.assertTrue(data['values_this_week'])
            self.assertTrue(data['questions_to_discuss'])
            statuses = {s['verification_status'] for s in data['sources']}
            self.assertLessEqual(statuses, {'reviewed', 'seeded'})
            types = {s['type'] for s in data['sources']}
            self.assertLessEqual({'hadith', 'verse'}, types)

    def test_ensure_gives_this_week_sources_and_is_idempotent(self):
        from session_moral_context.models import ServedReference
        call_command('seed_demo', '--ensure', stdout=StringIO())
        self.check()
        n = ServedReference.objects.count()
        call_command('seed_demo', '--ensure', stdout=StringIO())
        self.assertEqual(ServedReference.objects.count(), n)
        self.check()

    def test_monday(self):
        from datetime import datetime, timezone as tz
        from unittest.mock import patch
        with patch('django.utils.timezone.now',
                   return_value=datetime(2026, 10, 5, 0, 30, tzinfo=tz.utc)):
            call_command('seed_demo', '--ensure', stdout=StringIO())
            self.check()

    def test_empty_bank_skips(self):
        from session_moral_context.models import ContentItem
        ContentItem.objects.all().delete()
        call_command('seed_demo', '--ensure', stdout=StringIO())
        self.assertEqual(self.insights()['sources'], [])

    def _strip(self):
        from conversation.models import TurnAudit
        from session_moral_context.models import ServedReference
        ServedReference.objects.all().delete()
        TurnAudit.objects.all().delete()
        SessionReport.objects.update(sources_used=[])
        Session.objects.update(started_at=timezone.now() - timedelta(days=8))

    def test_topup_repairs_old_family(self):
        call_command('seed_demo', '--ensure', stdout=StringIO())
        self._strip()
        call_command('seed_demo', '--ensure', stdout=StringIO())
        self.check()

    def test_topup_skips_leased_slot(self):
        from session_moral_context.models import ServedReference
        call_command('seed_demo', '--ensure', stdout=StringIO())
        self._strip()
        cache.set(services.LEASE_KEY.format(slot=1), 'x:1', 600)
        call_command('seed_demo', '--ensure', stdout=StringIO())
        _, child = services.get_family(1)
        self.assertFalse(ServedReference.objects.filter(session__child=child).exists())

    def test_topup_skips_active_session(self):
        from session_moral_context.models import ServedReference
        call_command('seed_demo', '--ensure', stdout=StringIO())
        self._strip()
        Session.objects.update(status='active')
        call_command('seed_demo', '--ensure', stdout=StringIO())
        self.assertFalse(ServedReference.objects.exists())
