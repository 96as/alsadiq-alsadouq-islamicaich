"""Token refresh that refuses demo tokens whose lease has ended.

Wired in through SIMPLE_JWT['TOKEN_REFRESH_SERIALIZER']. Without it a demo
visitor could keep refreshing (each rotation is a fresh 7-day token) after
their family was handed to someone else.
"""
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings

from .authentication import check_demo_lease


class DemoLeaseTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = self.token_class(attrs['refresh'])
        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        if user_id is not None:
            username = (
                get_user_model()
                .objects.filter(**{api_settings.USER_ID_FIELD: user_id})
                .values_list('username', flat=True)
                .first()
            )
            check_demo_lease(username, refresh)
        return super().validate(attrs)
