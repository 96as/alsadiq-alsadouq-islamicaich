"""Authorization sweep, round 2: holes found outside the round 1 routes."""

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache, caches
from django.test import TestCase
from rest_framework.test import APIClient

from authentication.models import ChildProfile
from gamification.models import ChildQuestProgress, Points, Quest
from gamification.services import complete_quest_progress

User = get_user_model()


class QuestDoubleAwardTests(TestCase):
    def test_second_completion_of_a_stale_row_awards_nothing(self):
        """Child fires two PATCH /api/gamification/quests/<id>/complete/ at once.

        Both requests load the progress row while it is still unfinished, both pass the
        "already completed" check in the view, and both reach complete_quest_progress, so
        the child is paid the reward twice (and N times for N parallel requests). The
        second call here holds the stale in-memory row, exactly like the losing request.
        """
        child_user = User.objects.create_user(username='race_child', password='x', is_child=True)
        child = ChildProfile.objects.create(user=child_user, nickname='R', gender='male', birth_year=2015)
        quest = Quest.objects.create(
            title='Self quest', reward_points=10, quest_type='real_world', verification_method='self',
        )
        progress = ChildQuestProgress.objects.create(child=child, quest=quest, status='in_progress')
        stale = ChildQuestProgress.objects.get(pk=progress.pk)

        first = complete_quest_progress(progress, verified_by='child')
        second = complete_quest_progress(stale, verified_by='child')

        self.assertIsNotNone(first['points'])
        self.assertIsNone(second['points'])
        self.assertEqual(second['new_badges'], [])
        self.assertEqual(Points.objects.get(child=child).total, 10)


class PasswordResetEmailCaseTests(TestCase):
    def setUp(self):
        cache.clear()
        caches['throttle'].clear()
        self.addCleanup(cache.clear)
        self.addCleanup(caches['throttle'].clear)

    def test_registration_refuses_an_email_that_differs_only_by_case(self):
        """Attacker registers VICTIM@x.test while victim@x.test exists.

        Registration compared emails case-sensitively, so both accounts exist. The
        reset view looks the address up case-insensitively with .get(), which then
        raises MultipleObjectsReturned: the victim's "forgot password" returns a 500
        for as long as the lookalike account exists.
        """
        User.objects.create_user(username='victim', password='x', email='victim@x.test', is_parent=True)
        res = APIClient().post('/api/auth/register/parent/', {
            'username': 'lookalike', 'password': 'S3cure-pass-91', 'email': 'VICTIM@x.test',
            'first_name': 'A', 'last_name': 'B',
        }, format='json')
        self.assertEqual(res.status_code, 400, res.content)
        self.assertFalse(User.objects.filter(username='lookalike').exists())

    def test_reset_request_survives_existing_duplicate_emails(self):
        """Accounts that already differ only by case must not turn the reset into a 500."""
        User.objects.create_user(username='dup_a', password='x', email='dup@x.test', is_parent=True)
        User.objects.create_user(username='dup_b', password='x', email='DUP@x.test', is_parent=True)
        res = APIClient().post('/api/auth/password-reset/', {'email': 'dup@x.test'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)


class QuestBadBodyTests(TestCase):
    """Odd JSON bodies must be a 400, not an unhandled 500."""

    def setUp(self):
        cache.clear()
        caches['throttle'].clear()
        self.addCleanup(cache.clear)
        self.addCleanup(caches['throttle'].clear)
        from authentication.models import ParentChildLink, ParentProfile
        p_user = User.objects.create_user(username='bb_parent', password='x', is_parent=True)
        c_user = User.objects.create_user(username='bb_child', password='x', is_child=True)
        parent = ParentProfile.objects.create(user=p_user, name='P')
        child = ChildProfile.objects.create(user=c_user, nickname='C', gender='male', birth_year=2015)
        ParentChildLink.objects.create(parent=parent, child=child, consent_status='approved')
        quest = Quest.objects.create(
            title='Parent quest', reward_points=5, quest_type='real_world', verification_method='parent',
        )
        self.progress = ChildQuestProgress.objects.create(child=child, quest=quest, status='in_progress')
        self.p_user, self.c_user = p_user, c_user

    def test_child_complete_rejects_non_object_and_non_string_proof_note(self):
        """PATCH body [] (JSON array) or proof_note=5 hit AttributeError/TypeError -> 500."""
        client = APIClient()
        client.force_authenticate(user=self.c_user)
        url = f'/api/gamification/quests/{self.progress.pk}/complete/'
        for body in ([], {'proof_note': 5}, {'proof_note': ['x']}):
            with self.subTest(body=body):
                self.assertEqual(client.patch(url, body, format='json').status_code, 400)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, 'in_progress')

    def test_parent_verify_rejects_non_object_and_non_string_action(self):
        """PATCH body [] or action=5 hit AttributeError on .get/.lower() -> 500."""
        self.progress.status = 'pending_verification'
        self.progress.save(update_fields=['status'])
        client = APIClient()
        client.force_authenticate(user=self.p_user)
        url = f'/api/gamification/parent/quests/{self.progress.pk}/verify/'
        for body in ([], {'action': 5}, {'action': ['approve']}):
            with self.subTest(body=body):
                self.assertEqual(client.patch(url, body, format='json').status_code, 400)
