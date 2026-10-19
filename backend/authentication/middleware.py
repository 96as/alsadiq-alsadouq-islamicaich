"""Middleware for authentication-related side effects."""

from django.core.cache import cache
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from .models import ChildProfile

# Throttle DB writes: at most once per window per child user.
_CHILD_SEEN_CACHE_PREFIX = 'child_last_seen:'
_CHILD_SEEN_CACHE_SECONDS = 30


class UpdateChildLastSeenMiddleware(MiddlewareMixin):
    """Bump ChildProfile.last_seen_at when a child hits the API (app activity)."""

    def process_response(self, request, response):
        user = getattr(request, 'user', None)
        if (
            not user
            or not user.is_authenticated
            or not getattr(user, 'is_child', False)
            or response.status_code >= 500
        ):
            return response

        if not hasattr(user, 'child_profile'):
            return response

        cache_key = f'{_CHILD_SEEN_CACHE_PREFIX}{user.pk}'
        if cache.get(cache_key):
            return response

        now = timezone.now()
        ChildProfile.objects.filter(user_id=user.pk).update(last_seen_at=now)
        cache.set(cache_key, 1, _CHILD_SEEN_CACHE_SECONDS)
        return response
