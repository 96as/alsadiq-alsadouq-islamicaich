"""DRF throttles that count in the shared "throttle" cache.

DRF's stock throttles use the default cache, which is LocMem: one counter set per gunicorn
worker, so with 3 workers every limit is about 3x. The "throttle" alias (settings.py) is Redis
when REDIS_URL / REDIS_HOST is set, so the limit holds across workers; LocMem otherwise.

Degrades, not open: if the cache raises (Redis blip), the same throttle is evaluated against a
per-process LocMem fallback and a warning (exception type only) is logged. Login and the demo
stay up and limits still hold, but per worker (about N x looser with N workers) until Redis is
back. Redis calls time out after 0.5s (settings.py), which bounds the added latency.
"""
import logging

from django.core.cache import caches
from django.core.cache.backends.locmem import LocMemCache
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle

logger = logging.getLogger(__name__)

# Used only while the shared cache is erroring. Big enough that culling does not evict counters.
_fallback = LocMemCache('alsadiq-throttle-fallback', {'OPTIONS': {'MAX_ENTRIES': 100_000}})


class SharedCacheThrottleMixin:
    _degraded = False

    @property
    def cache(self):
        return _fallback if self._degraded else caches['throttle']

    def allow_request(self, request, view):
        self._degraded = False
        try:
            return super().allow_request(request, view)
        except Exception as exc:  # noqa: BLE001 - a cache outage must not become a 500
            logger.warning("Throttle %s using per-process fallback, shared cache failed: %s",
                           type(self).__name__, type(exc).__name__)
            self._degraded = True
            return super().allow_request(request, view)


class SharedAnonRateThrottle(SharedCacheThrottleMixin, AnonRateThrottle):
    pass


class SharedUserRateThrottle(SharedCacheThrottleMixin, UserRateThrottle):
    pass


class SharedScopedRateThrottle(SharedCacheThrottleMixin, ScopedRateThrottle):
    pass
