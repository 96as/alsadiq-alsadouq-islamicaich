"""
Notes Section for the file:
- SessionStartThrottle: at most N session starts per hour per user (default 6,
  DEMO_SESSION_START_PER_HOUR), next to the existing 5/minute login throttle.

- Counted in the shared "guards" cache (Redis when REDIS_HOST is set, see settings.py), so
  the limit holds across all gunicorn workers. A per-process cache would give every worker
  its own allowance.
- Judge accounts get JUDGE_SESSION_START_PER_HOUR (default 20) instead.
- Off while the demo guards are off (see conversation.demo_guards.guards_active).
- Fails open: if the cache is unreachable the request is allowed and one error is logged.
"""
import logging

from django.core.cache import caches
from rest_framework.throttling import SimpleRateThrottle

from config.throttling import SharedUserRateThrottle

from conversation import demo_guards
from demo.accounts import is_judge_user

logger = logging.getLogger(__name__)


class SessionStartThrottle(SimpleRateThrottle):
    scope = "session_start"

    @property
    def cache(self):
        return caches["guards"]

    def get_rate(self):
        per_hour = demo_guards.config().session_start_per_hour
        return f"{per_hour}/hour" if per_hour > 0 else None

    def get_cache_key(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return None
        return self.cache_format % {"scope": self.scope, "ident": request.user.pk}

    def allow_request(self, request, view):
        if is_judge_user(request.user):
            per_hour = demo_guards.config().judge_session_start_per_hour
            self.rate = f"{per_hour}/hour" if per_hour > 0 else None
            self.num_requests, self.duration = self.parse_rate(self.rate)
        try:
            return super().allow_request(request, view)
        except Exception:  # noqa: BLE001 - never block a child because a cache is down
            logger.exception("Session start throttle skipped: the cache is unreachable")
            return True


class StartSessionRateThrottle(SharedUserRateThrottle):
    """Always-on per-user cap on session starts (default 30/hour, SESSION_START_USER_RATE).

    Every start creates a LiveKit room, which costs money. SessionStartThrottle above is
    only active in demo mode; this one protects a normal deployment too.
    """
    scope = 'session_start_user'
