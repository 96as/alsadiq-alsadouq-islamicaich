"""Access-control checks for the superadmin API.

The API is read-only (edits belong in Django /admin), so the contract under test is
who may reach it: superusers only, on every route. Staff, parents, children and
anonymous callers get 401/403 for any method; a superuser gets 200 on reads and 405
on every write.
"""

from django.contrib.auth import get_user_model
from django.core.cache import cache, caches
from django.test import TestCase
from rest_framework.test import APIClient

from superadmin.urls import router

METHODS = ('get', 'post', 'patch', 'put', 'delete')


class SuperAdminAccessTests(TestCase):
    def setUp(self):
        user = get_user_model()
        self.victim = user.objects.create_user(
            username='audit_victim', password='testpass123', first_name='Original',
        )
        self.callers = {
            'anonymous': None,
            'staff': user.objects.create_user(
                username='audit_staff', password='testpass123', is_staff=True,
            ),
            'parent': user.objects.create_user(
                username='audit_parent', password='testpass123', is_parent=True,
            ),
            'child': user.objects.create_user(
                username='audit_child', password='testpass123', is_child=True,
            ),
        }

    def client_for(self, caller):
        client = APIClient()
        if caller is not None:
            client.force_authenticate(user=caller)
        return client

    def test_only_superusers_reach_any_route_with_any_method(self):
        for who, caller in self.callers.items():
            client = self.client_for(caller)
            for prefix, _viewset, _basename in router.registry:
                urls = [f'/superadmin/api/{prefix}/']
                if prefix != 'stats':  # list-only ViewSet, no detail route
                    urls.append(f'/superadmin/api/{prefix}/{self.victim.pk}/')
                for url in urls:
                    for method in METHODS:
                        with self.subTest(caller=who, url=url, method=method):
                            response = getattr(client, method)(url, {}, format='json')
                            self.assertIn(response.status_code, (401, 403))

    def test_superuser_positive_control(self):
        # Proves the 401/403 above come from the permission check, not a broken route.
        admin = get_user_model().objects.create_superuser(username='audit_root', password='testpass123')
        self.assertEqual(self.client_for(admin).get('/superadmin/api/users/').status_code, 200)

    def test_superuser_reads_everywhere_and_cannot_write_anywhere(self):
        """Hole: a stolen superuser JWT (or the dashboard XSS) could rewrite points, quest
        status, consent_status or is_superuser, or delete rows, through the superadmin API.
        It now only reads."""
        admin = get_user_model().objects.create_superuser(username='audit_root2', password='testpass123')
        client = self.client_for(admin)
        for prefix, _viewset, _basename in router.registry:
            cache.clear()  # ~11 calls per route would trip the 60/min user throttle
            caches['throttle'].clear()  # DRF counters live in this alias, not in default
            urls = [f'/superadmin/api/{prefix}/']
            if prefix != 'stats':
                urls.append(f'/superadmin/api/{prefix}/{self.victim.pk}/')
            self.assertEqual(client.get(urls[0]).status_code, 200, prefix)
            for url in urls:
                for method in ('post', 'patch', 'put', 'delete'):
                    with self.subTest(url=url, method=method):
                        self.assertEqual(getattr(client, method)(url, {}, format='json').status_code, 405)
        self.assertEqual(client.get(f'/superadmin/api/users/{self.victim.pk}/').status_code, 200)

    def test_superuser_patch_does_not_change_a_user_record(self):
        admin = get_user_model().objects.create_superuser(username='audit_root3', password='testpass123')
        self.client_for(admin).patch(
            f'/superadmin/api/users/{self.victim.pk}/', {'first_name': 'Changed'}, format='json',
        )
        self.victim.refresh_from_db()
        self.assertEqual(self.victim.first_name, 'Original')

    def test_non_superuser_cannot_change_a_user_record(self):
        for who, caller in self.callers.items():
            with self.subTest(caller=who):
                self.client_for(caller).patch(
                    f'/superadmin/api/users/{self.victim.pk}/',
                    {'first_name': 'Changed', 'is_superuser': True}, format='json',
                )
                self.victim.refresh_from_db()
                self.assertEqual(self.victim.first_name, 'Original')
                self.assertFalse(self.victim.is_superuser)


class DashboardEscapingTests(TestCase):
    def test_every_api_derived_innerhtml_value_is_escaped(self):
        """Stored XSS: a child sends a message whose text is <img src=x onerror=...>.

        The dashboard put row values and error text into innerHTML unescaped, so the
        markup ran in the superuser's browser, where the JWT sits in sessionStorage.
        """
        from django.template.loader import render_to_string

        html = render_to_string('superadmin/dashboard.html')
        self.assertIn('function esc(', html)
        self.assertNotIn('${val}</td>', html)
        self.assertNotIn('${e.message}', html)
        self.assertIn('${esc(val)}', html)
        self.assertIn('${esc(e.message)}', html)
        self.assertIn('${esc(k.replace', html)


class DashboardIsReadOnlyTests(TestCase):
    def test_dashboard_has_no_edit_create_or_delete_ui(self):
        from django.template.loader import render_to_string

        html = render_to_string('superadmin/dashboard.html')
        for marker in ("api('PATCH'", "api('POST'", "api('DELETE'", 'formModal', 'deleteModal',
                       'btnCreate', 'openEdit', 'openDelete', 'fields:'):
            self.assertNotIn(marker, html, marker)
