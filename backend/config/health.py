"""Uptime-monitor endpoint: GET or HEAD /api/health/ (no auth, no throttle).

Checks the database and Redis. Returns 200 with {"status": "ok"} when every
check passes, 503 with {"status": "degraded"} otherwise. Error details are
never returned, only "ok", "error" or "skipped" per check. HEAD is allowed
because some uptime monitors use it by default.
"""
import logging
import os

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

logger = logging.getLogger(__name__)


def _check_db() -> str:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return "ok"
    except Exception:
        logger.exception("health: database check failed")
        return "error"


def _check_redis() -> str:
    host = os.getenv("REDIS_HOST", "").strip()
    if not host:
        # Not configured (plain dev / test runs): nothing to check.
        return "skipped"
    client = None
    try:
        import redis

        client = redis.Redis(
            host=host,
            port=int(os.getenv("REDIS_PORT", "6379")),
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        return "ok"
    except Exception:
        logger.exception("health: redis check failed")
        return "error"
    finally:
        # One short-lived connection per check; don't leave it to the GC.
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


@never_cache
@require_safe
def health(request):
    checks = {"database": _check_db(), "redis": _check_redis()}
    healthy = all(value in ("ok", "skipped") for value in checks.values())
    return JsonResponse(
        {"status": "ok" if healthy else "degraded", "checks": checks},
        status=200 if healthy else 503,
    )
