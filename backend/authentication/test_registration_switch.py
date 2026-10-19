"""REGISTRATION_OPEN=0 closes public sign-up; existing accounts still sign in."""
from django.test import override_settings
from rest_framework.test import APITestCase

URL = '/api/auth/register/parent/'


class RegistrationSwitchTests(APITestCase):
    @override_settings(REGISTRATION_OPEN=False)
    def test_closed_refuses_with_judge_message(self):
        resp = self.client.post(URL, {'username': 'newparent'}, format='json')
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['code'], 'registration_closed')
        self.assertIn('judge', resp.json()['detail'])
        self.assertTrue(resp.json()['detail_ar'])

    @override_settings(REGISTRATION_OPEN=True)
    def test_open_still_validates_as_before(self):
        resp = self.client.post(URL, {'username': 'newparent'}, format='json')
        self.assertEqual(resp.status_code, 400)  # missing fields, not refused
