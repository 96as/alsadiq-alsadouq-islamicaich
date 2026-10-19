"""seed_judges: persistent judge accounts, kept out of the demo pool, with their own caps."""
import os
import stat
import tempfile
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from authentication.models import ChildProfile, ParentChildLink, ParentProfile
from conversation import demo_guards
from conversation.models import Message, Session
from conversation.test_demo_guards import GuardTestCase
from gamification.models import ChildBadge, ChildQuestProgress, Quest
from reporting.models import SessionReport, WeeklySummary
from session_moral_context.models import HADITH_REQUIRED_GRADE, ContentItem, ServedReference

from . import services
from .accounts import is_judge_user, is_reserved_username
from .authentication import check_demo_lease
from .management.commands.seed_judges import read_passwords

User = get_user_model()
TEST_CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
    'throttle': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'j-throttle'},
}


def _bank():
    for k in range(3):
        ContentItem.objects.create(
            type='hadith', arabic_text='نص تجريبي', english_text=f'PLACEHOLDER {k}',
            translation_name='t', book='b', number=str(k), grade=HADITH_REQUIRED_GRADE, grader='g',
            source_site='dorar.net', source_url=f'https://dorar.net/placeholder/{k}',
            content_level='A', verification_status='reviewed')


@override_settings(DEMO_MODE=True, DEMO_POOL_SIZE=2, CACHES=TEST_CACHES)
class SeedJudgesTests(TestCase):
    def setUp(self):
        cache.clear()
        _bank()
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = os.path.join(self.dir.name, 'judges.txt')

    def seed(self, *extra, count=5):
        out, err = StringIO(), StringIO()
        call_command('seed_judges', '--count', str(count), '--password-file', self.path, *extra,
                     stdout=out, stderr=err)
        return out.getvalue() + err.getvalue()

    def test_five_parents_each_with_an_arabic_and_an_english_child(self):
        self.seed()
        for n in range(1, 6):
            parent = ParentProfile.objects.get(user__username=f'judge{n}')
            kids = {c.user.username: c for c in ChildProfile.objects.filter(
                parents__parent=parent, parents__consent_status='approved')}
            self.assertEqual(set(kids), {f'judge{n}-ar', f'judge{n}-en'})
            ar, en = kids[f'judge{n}-ar'], kids[f'judge{n}-en']
            self.assertEqual((ar.nickname, ar.language_preference), ('سلمى', 'ar'))
            self.assertEqual((en.nickname, en.language_preference), ('Adam', 'en'))
            for child in (ar, en):
                self.assertEqual(Session.objects.filter(child=child).count(), 3)
                self.assertEqual(SessionReport.objects.filter(session__child=child).count(), 3)
                self.assertTrue(WeeklySummary.objects.filter(child=child, parent=parent).exists())
                self.assertTrue(ServedReference.objects.filter(session__child=child).exists())
                self.assertEqual(
                    set(ChildQuestProgress.objects.filter(child=child).values_list('status', flat=True)),
                    {'completed', 'pending_verification', 'in_progress', 'not_started'})
            # Each child's seeded words are in its own language.
            self.assertTrue(all(m.language == 'en' for m in Message.objects.filter(session__child=en)))
            self.assertIn('Adam', WeeklySummary.objects.get(child=en).summary)
            self.assertIn('Al-Sadiq', WeeklySummary.objects.get(child=en).summary)
            en_titles = set(ChildQuestProgress.objects.filter(child=en).values_list('quest__title', flat=True))
            self.assertIn('Help at home', en_titles)
            self.assertIn('ساعد في البيت', set(
                ChildQuestProgress.objects.filter(child=ar).values_list('quest__title', flat=True)))
        self.assertEqual(ParentProfile.objects.count(), 5)
        self.assertEqual(ChildProfile.objects.count(), 10)

    def test_badges_are_awarded_by_the_real_engine(self):
        self.seed(count=1)
        child = ChildProfile.objects.get(user__username='judge1-en')
        # Some earned, some still locked (the migration seeds the badge catalogue).
        self.assertTrue(ChildBadge.objects.filter(child=child).exists())
        from gamification.models import Badge
        self.assertGreater(Badge.objects.count(), ChildBadge.objects.filter(child=child).count())

    def test_rerun_refreshes_without_duplicates_and_keeps_passwords(self):
        self.seed()
        first = read_passwords(self.path)
        counts = (User.objects.count(), ParentChildLink.objects.count(), Session.objects.count(),
                  ChildQuestProgress.objects.count(), Quest.objects.count(), WeeklySummary.objects.count(),
                  ChildBadge.objects.count())
        child = ChildProfile.objects.get(user__username='judge2-en')
        Session.objects.create(child=child, livekit_room_name='judge-live-1', status='ended')
        ChildProfile.objects.filter(pk=child.pk).update(nickname='Changed', language_preference='ar')

        self.seed()
        self.assertEqual(read_passwords(self.path), first)
        self.assertEqual(counts, (
            User.objects.count(), ParentChildLink.objects.count(), Session.objects.count(),
            ChildQuestProgress.objects.count(), Quest.objects.count(), WeeklySummary.objects.count(),
            ChildBadge.objects.count()))
        child.refresh_from_db()
        self.assertEqual((child.nickname, child.language_preference), ('Adam', 'en'))
        self.assertTrue(User.objects.get(username='judge2-en').check_password(first['judge2-en']))

    def test_rerun_drops_a_child_a_judge_added(self):
        self.seed(count=1)
        parent = ParentProfile.objects.get(user__username='judge1')
        extra = ChildProfile.objects.create(
            user=User.objects.create_user(username='kid-x', is_child=True), nickname='x', gender='male')
        ParentChildLink.objects.create(parent=parent, child=extra, consent_status='approved')
        self.seed(count=1)
        self.assertEqual(ParentChildLink.objects.filter(parent=parent).count(), 2)

    def test_password_file_is_600_and_no_password_is_printed(self):
        output = self.seed()
        mode = stat.S_IMODE(os.stat(self.path).st_mode)
        self.assertEqual(mode, 0o600)
        passwords = read_passwords(self.path)
        self.assertEqual(len(passwords), 15)
        self.assertEqual(len(set(passwords.values())), 15)
        for username, password in passwords.items():
            self.assertGreaterEqual(len(password), 16)
            self.assertNotIn(password, output)
            user = User.objects.get(username=username)
            self.assertTrue(user.check_password(password))

    def test_an_existing_file_with_loose_permissions_ends_up_600(self):
        with open(self.path, 'w') as f:
            f.write('judge1\told-password-1234\tparent\n')
        os.chmod(self.path, 0o644)
        self.seed(count=1)
        self.assertEqual(stat.S_IMODE(os.stat(self.path).st_mode), 0o600)
        self.assertEqual(read_passwords(self.path)['judge1'], 'old-password-1234')

    def test_rotate_gives_new_passwords_and_signs_judges_out(self):
        self.seed(count=1)
        before = read_passwords(self.path)
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
        RefreshToken.for_user(User.objects.get(username='judge1'))
        self.seed('--rotate-passwords', count=1)
        after = read_passwords(self.path)
        self.assertTrue(all(before[u] != after[u] for u in before))
        self.assertEqual(BlacklistedToken.objects.count(), 1)

    def test_refuses_to_take_over_an_account_that_is_not_a_judge(self):
        User.objects.create_user(username='judge1', email='someone@example.com', password='x' * 12,
                                 is_parent=True)
        with self.assertRaises(CommandError):
            self.seed(count=1)
        self.assertTrue(User.objects.get(username='judge1').check_password('x' * 12))

    def test_judges_are_not_in_the_demo_pool(self):
        call_command('seed_demo', stdout=StringIO())
        self.seed(count=2)
        judge_sessions = Session.objects.filter(child__user__username__startswith='judge').count()
        self.assertEqual(services.pool_slots(), [1, 2])
        services.seed_pool()          # full demo reset
        services.reset_expired()      # demo cleanup
        self.assertEqual(
            Session.objects.filter(child__user__username__startswith='judge').count(), judge_sessions)
        judge = User.objects.get(username='judge1-ar')
        self.assertTrue(is_judge_user(judge))
        self.assertFalse(is_judge_user(User.objects.get(username='demo-child-1')))
        self.assertIsNone(check_demo_lease(judge.username, None))  # no lease needed
        self.assertTrue(judge.has_usable_password())

    def test_a_lower_count_keeps_the_other_judges_passwords(self):
        self.seed(count=3)
        before = read_passwords(self.path)
        self.seed(count=2)
        self.assertEqual(read_passwords(self.path), before)

    def test_a_judge_username_without_the_marker_email_is_not_a_judge(self):
        old = User.objects.create_user(username='judge7', email='someone@example.com', is_parent=True)
        self.assertFalse(is_judge_user(old))

    def test_nobody_can_register_a_judge_username(self):
        self.assertTrue(is_reserved_username('judge7'))
        self.assertTrue(is_reserved_username('Judge1-en'))
        response = APIClient().post('/api/auth/register/parent/', {
            'username': 'judge42', 'password': 'Str0ng-pass-123', 'email': 'a@example.com',
            'first_name': 'a', 'last_name': 'b'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username='judge42').exists())


class JudgeCapTests(GuardTestCase):
    """Judges get JUDGE_DAILY_SESSIONS / JUDGE_SESSION_START_PER_HOUR, not the demo caps."""

    def setUp(self):
        super().setUp()
        pipeline = mock.patch('reporting.services.run_post_session_pipeline')
        pipeline.start()
        self.addCleanup(pipeline.stop)
        self.url = reverse('conversation:start_session')

    def _child(self, username):
        email = f'{username}@judges.invalid' if username.startswith('judge') else ''
        user = User.objects.create_user(username=username, password='pass12345', is_child=True,
                                        email=email)
        ChildProfile.objects.create(user=user, nickname='Kid', gender='male', birth_year=2015,
                                    language_preference='en')
        client = APIClient()
        client.force_authenticate(user)
        return client

    def test_defaults(self):
        cfg = demo_guards.config()
        self.assertEqual((cfg.judge_daily_sessions, cfg.judge_session_start_per_hour), (30, 20))

    def test_daily_cap_is_per_kind_of_account(self):
        for _ in range(30):
            demo_guards.check_session_start(7, judge=True)
        with self.assertRaises(demo_guards.GuardDenied):
            demo_guards.check_session_start(7, judge=True)
        for _ in range(3):
            demo_guards.check_session_start(8)
        with self.assertRaises(demo_guards.GuardDenied):
            demo_guards.check_session_start(8)

    @mock.patch.dict(os.environ, {'JUDGE_SESSION_START_PER_HOUR': '0'})
    def test_a_judge_child_passes_the_demo_caps_and_stops_at_its_own(self):
        demo = self._child('demo_kid')
        statuses = [demo.post(self.url).status_code for _ in range(4)]
        self.assertEqual(statuses[-1], 429)  # the demo daily cap is 3
        with mock.patch.dict(os.environ, {'JUDGE_DAILY_SESSIONS': '12'}):
            judge = self._child('judge1-en')
            statuses = [judge.post(self.url).status_code for _ in range(13)]
        self.assertTrue(all(s in (200, 201) for s in statuses[:12]), statuses)
        self.assertEqual(statuses[12], 429)

    @mock.patch.dict(os.environ, {'JUDGE_DAILY_SESSIONS': '0'})
    def test_judge_start_throttle(self):
        judge = self._child('judge1-ar')
        statuses = [judge.post(self.url).status_code for _ in range(21)]
        self.assertTrue(all(s in (200, 201) for s in statuses[:20]), statuses)
        self.assertEqual(statuses[20], 429)
        self.assertEqual(judge.post(self.url).json()['code'], 'rate_limited')
