"""The LiveKit webhook is signature-verified, so it must not sit behind the anonymous throttle."""
import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache, caches
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from livekit.api import AccessToken
from rest_framework.test import APIClient

from authentication.models import ChildProfile
from conversation.models import Session

User = get_user_model()


def _signed_headers(body: str) -> dict:
    import base64
    import hashlib

    token = (
        AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_sha256(base64.b64encode(hashlib.sha256(body.encode()).digest()).decode())
        .to_jwt()
    )
    return {'HTTP_AUTHORIZATION': token}


class LiveKitWebhookThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        caches['throttle'].clear()
        self.client = APIClient()
        user = User.objects.create_user(username='wh_throttle', password='x', is_child=True)
        child = ChildProfile.objects.create(
            user=user, nickname='WhKid', gender='female', birth_year=2016,
        )
        self.session = Session.objects.create(
            child=child, status='active', livekit_room_name='session_wh_throttle',
        )

    def test_forty_bad_signatures_are_all_401_never_429(self):
        url = reverse('conversation:livekit_webhook')
        codes = [
            self.client.post(
                url, data='{}', content_type='application/json',
                HTTP_AUTHORIZATION='Bearer not-a-real-token',
            ).status_code
            for _ in range(40)
        ]
        self.assertEqual(set(codes), {401})

    @patch('reporting.services.run_post_session_pipeline')
    def test_signed_room_finished_ends_session_after_a_burst(self, _pipeline):
        url = reverse('conversation:livekit_webhook')
        for _ in range(40):
            self.client.post(
                url, data='{}', content_type='application/json',
                HTTP_AUTHORIZATION='Bearer nope',
            )
        body = json.dumps({'event': 'room_finished', 'room': {'name': 'session_wh_throttle'}})
        resp = self.client.post(
            url, data=body, content_type='application/webhook+json', **_signed_headers(body),
        )
        self.assertEqual(resp.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'ended')
