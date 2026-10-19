"""Security regression checks for LiveKit room access."""

from types import SimpleNamespace

import jwt
from django.test import SimpleTestCase

from conversation.services import _child_livekit_token


class LiveKitTokenLifetimeTests(SimpleTestCase):
    def test_unlimited_session_token_cannot_be_reused_hours_later(self):
        child = SimpleNamespace(user_id=123, nickname="test-child")
        token = _child_livekit_token(child, "session_456", ttl_seconds=None)
        claims = jwt.decode(token, options={"verify_signature": False})
        self.assertEqual(claims["video"]["room"], "session_456")
        self.assertLessEqual(claims["exp"] - claims["nbf"], 600)

    def test_token_does_not_carry_the_child_nickname(self):
        child = SimpleNamespace(user_id=123, nickname="test-child")
        token = _child_livekit_token(child, "session_456")
        claims = jwt.decode(token, options={"verify_signature": False})
        self.assertNotIn("test-child", str(claims))
        self.assertEqual(claims["video"]["room"], "session_456")
        self.assertFalse(claims["video"].get("roomAdmin"))
