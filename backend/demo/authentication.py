"""JWT checks that end a demo visitor's access when their lease ends.

Demo families are shared by visitors in turn. simplejwt alone would let a
token outlive the lease: a refresh rotation mints a 7-day refresh token and a
fresh 30-minute access token, so the last visitor could still read the next
visitor's family. Here a demo account's token only works while the lease it
was minted for (its ``demo_lease`` claim) is still that family's live lease.

Non-demo users pay one regex on the username and nothing else.
The refresh side lives in ``demo.serializers``.
"""
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from .accounts import demo_slot


def check_demo_lease(username, token):
    """Raise InvalidToken if a demo account's token is not for the live lease."""
    slot = demo_slot(username)
    if slot is None:
        return
    from . import services  # lazy: services imports models

    lease_id = token.get('demo_lease') if token is not None else None
    if not settings.DEMO_MODE or not services.lease_holder_matches(slot, lease_id):
        raise InvalidToken('This demo has ended. Start a new one.')


class DemoLeaseJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, token = result
            check_demo_lease(user.username, token)
        return result
