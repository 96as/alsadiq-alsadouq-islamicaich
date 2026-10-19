"""Cross-family checks for every public API route that accepts an object ID."""

from django.contrib.auth import get_user_model
from django.core.cache import cache, caches
from django.test import TestCase
from rest_framework.test import APIClient

from authentication.models import ChildProfile, ParentChildLink, ParentProfile
from content_safety.models import Alert
from conversation.models import Message, Session
from gamification.models import ChildQuestProgress, Quest


class CrossFamilyAccessTests(TestCase):
    @staticmethod
    def family(name):
        user = get_user_model()
        parent_user = user.objects.create_user(
            username=f'{name}_parent', password='testpass123', is_parent=True,
        )
        child_user = user.objects.create_user(
            username=f'{name}_child', password='testpass123', is_child=True,
        )
        parent = ParentProfile.objects.create(user=parent_user, name=name)
        child = ChildProfile.objects.create(
            user=child_user, nickname=name, gender='male', birth_year=2015,
        )
        link = ParentChildLink.objects.create(
            parent=parent, child=child, consent_status='approved',
        )
        return parent, child, link

    def setUp(self):
        # DRF throttle counters live in the cache and user ids repeat between tests.
        cache.clear()
        caches['throttle'].clear()
        self.addCleanup(cache.clear)
        self.addCleanup(caches['throttle'].clear)
        self.parent, self.child, self.link = self.family('own')
        self.other_parent, self.other_child, self.other_link = self.family('other')
        self.session = Session.objects.create(
            child=self.other_child, livekit_room_name='other-family-room',
        )
        Message.objects.create(
            session=self.session, sender='child', content='private child text',
        )
        self.alert = Alert.objects.create(
            parent=self.other_parent, session=self.session,
            alert_type='safety', description='other family alert',
        )
        quest = Quest.objects.create(
            title='Other family quest', reward_points=10,
            quest_type='real_world', verification_method='parent',
        )
        self.progress = ChildQuestProgress.objects.create(
            child=self.other_child, quest=quest, status='pending_verification',
        )
        self.client = APIClient()

    def test_parent_id_routes_reject_another_family(self):
        self.client.force_authenticate(user=self.parent.user)
        routes = (
            ('/api/reporting/insights/{}/', 403),
            ('/api/reporting/dashboard/{}/', 403),
            ('/api/conversation/parent/children/{}/summary/', 404),
            ('/api/gamification/parent/children/{}/quests/', 403),
        )
        for template, expected in routes:
            with self.subTest(route=template):
                response = self.client.get(template.format(self.other_child.pk))
                self.assertEqual(response.status_code, expected)
                self.assertNotIn(b'private child text', response.content)

    def test_child_id_routes_reject_another_child(self):
        self.client.force_authenticate(user=self.child.user)
        messages = self.client.get(
            f'/api/conversation/sessions/{self.session.pk}/messages/'
        )
        self.assertEqual(messages.status_code, 200)
        self.assertEqual(messages.data, [])
        end = self.client.post(f'/api/conversation/sessions/{self.session.pk}/end/')
        self.assertEqual(end.status_code, 404)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'active')
        complete = self.client.patch(
            f'/api/gamification/quests/{self.progress.pk}/complete/', {}, format='json',
        )
        self.assertEqual(complete.status_code, 404)

    def test_parent_object_id_routes_reject_another_family(self):
        self.client.force_authenticate(user=self.parent.user)
        mark_read = self.client.patch(f'/api/alerts/{self.alert.pk}/read/')
        self.assertEqual(mark_read.status_code, 404)
        self.alert.refresh_from_db()
        self.assertFalse(self.alert.is_read)
        verify = self.client.patch(
            f'/api/gamification/parent/quests/{self.progress.pk}/verify/',
            {'action': 'approve'}, format='json',
        )
        self.assertEqual(verify.status_code, 403)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, 'pending_verification')
        listed = self.client.get('/api/alerts/')
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data, [])

    def test_revoked_link_loses_parent_access(self):
        self.link.consent_status = 'revoked'
        self.link.save(update_fields=['consent_status'])
        self.client.force_authenticate(user=self.parent.user)
        routes = (
            ('/api/reporting/insights/{}/', 403),
            ('/api/reporting/dashboard/{}/', 403),
            ('/api/conversation/parent/children/{}/summary/', 404),
            ('/api/gamification/parent/children/{}/quests/', 403),
        )
        for template, expected in routes:
            with self.subTest(route=template):
                self.assertEqual(
                    self.client.get(template.format(self.child.pk)).status_code,
                    expected,
                )

    def test_parent_role_cannot_call_child_only_id_routes(self):
        self.client.force_authenticate(user=self.other_parent.user)
        self.assertEqual(
            self.client.get(f'/api/conversation/sessions/{self.session.pk}/messages/').status_code,
            403,
        )
        self.assertEqual(
            self.client.post(f'/api/conversation/sessions/{self.session.pk}/end/').status_code,
            403,
        )
        self.assertEqual(
            self.client.patch(f'/api/gamification/quests/{self.progress.pk}/complete/').status_code,
            403,
        )

    def test_non_approved_link_loses_alert_access(self):
        """IDOR: alerts were scoped by parent only, so a revoked or pending link kept
        reading (and marking read) alerts about a child the parent may no longer see."""
        own_session = Session.objects.create(
            child=self.child, livekit_room_name='own-family-room',
        )
        alert = Alert.objects.create(
            parent=self.parent, session=own_session,
            alert_type='safety', description='own child alert',
        )
        self.client.force_authenticate(user=self.parent.user)
        listed = self.client.get('/api/alerts/')
        self.assertEqual([a['id'] for a in listed.data], [alert.id])
        for status in ('revoked', 'pending'):
            with self.subTest(consent_status=status):
                self.link.consent_status = status
                self.link.save(update_fields=['consent_status'])
                listed = self.client.get('/api/alerts/')
                self.assertEqual(listed.status_code, 200)
                self.assertEqual(listed.data, [])
                self.assertNotIn(b'own child alert', listed.content)
                mark = self.client.patch(f'/api/alerts/{alert.pk}/read/')
                self.assertEqual(mark.status_code, 404)
                alert.refresh_from_db()
                self.assertFalse(alert.is_read)

    def test_anonymous_and_wrong_role_are_rejected_on_every_id_route(self):
        pk = self.other_child.pk
        parent_routes = (
            ('get', f'/api/reporting/insights/{pk}/'),
            ('get', f'/api/reporting/dashboard/{pk}/'),
            ('get', f'/api/conversation/parent/children/{pk}/summary/'),
            ('get', f'/api/gamification/parent/children/{pk}/quests/'),
            ('get', '/api/alerts/'),
            ('patch', f'/api/alerts/{self.alert.pk}/read/'),
            ('patch', f'/api/gamification/parent/quests/{self.progress.pk}/verify/'),
            ('get', '/api/auth/children/'),
        )
        child_routes = (
            ('get', f'/api/conversation/sessions/{self.session.pk}/messages/'),
            ('post', f'/api/conversation/sessions/{self.session.pk}/end/'),
            ('post', '/api/conversation/sessions/'),
            ('patch', f'/api/gamification/quests/{self.progress.pk}/complete/'),
            ('get', '/api/gamification/quests/'),
            ('get', '/api/gamification/badges/'),
            ('get', '/api/gamification/level/'),
            ('patch', '/api/auth/profile/child/'),
            ('post', '/api/auth/profile/child/password/'),
        )
        anon = APIClient()
        as_child = APIClient()
        as_child.force_authenticate(user=self.child.user)
        for method, url in parent_routes + child_routes:
            with self.subTest(caller='anonymous', url=url):
                self.assertEqual(getattr(anon, method)(url).status_code, 401)
        for method, url in parent_routes:
            with self.subTest(caller='child', url=url):
                self.assertEqual(getattr(as_child, method)(url).status_code, 403)
