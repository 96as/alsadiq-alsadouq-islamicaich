"""POST /api/demo/start and /api/demo/reset (only alive when DEMO_MODE=1)."""
import logging

from django.conf import settings
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.throttling import SharedScopedRateThrottle

from . import services

logger = logging.getLogger(__name__)

BUSY_AR = 'كل الغرف التجريبية مشغولة الآن. جرّب بعد قليل، وسنجهّز لك مكانًا.'
BUSY_EN = 'All demo rooms are busy right now. Please try again in a moment.'
EXPIRED_AR = 'انتهت مدة تجربتك. اضغط "جرّب الصديق" لتبدأ تجربة جديدة.'
EXPIRED_EN = 'Your demo time ended. Tap "Try Al-Sadiq" to start a new one.'


def _require_demo_mode():
    if not settings.DEMO_MODE:
        raise Http404()


class DemoStartView(APIView):
    """Lease a free synthetic family and hand back child + parent tokens."""

    permission_classes = [AllowAny]
    # No JWT parsing: a stale token in the browser must not turn this into a 401.
    authentication_classes = []
    throttle_classes = [SharedScopedRateThrottle]
    throttle_scope = 'demo_start'

    def initial(self, request, *args, **kwargs):
        _require_demo_mode()
        super().initial(request, *args, **kwargs)

    def post(self, request):
        try:
            payload = services.start_demo()
        except services.DemoBusy as busy:
            response = Response(
                {
                    'code': 'demo_busy',
                    'detail': BUSY_EN,
                    'message_en': BUSY_EN,
                    'message_ar': BUSY_AR,
                    'retry_after': busy.retry_after,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
            response['Retry-After'] = str(busy.retry_after)
            return response
        return Response(payload, status=status.HTTP_201_CREATED)


class DemoResetView(APIView):
    """'Start over': wipe the visitor's own family and re-seed it."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [SharedScopedRateThrottle]
    throttle_scope = 'demo_reset'

    def initial(self, request, *args, **kwargs):
        _require_demo_mode()
        super().initial(request, *args, **kwargs)

    def post(self, request):
        slot = services.slot_from_username(request.user.username)
        lease_id = None
        if request.auth is not None:
            try:
                lease_id = request.auth.get('demo_lease')
            except Exception:  # noqa: BLE001 - odd token types
                lease_id = None
        # A demo token whose lease is gone already fails authentication (401);
        # this 409 covers non-demo users and a lease that lapses mid-request.
        try:
            if not slot:
                raise services.LeaseLost()
            payload = services.restart_demo(slot, lease_id)
        except services.LeaseLost:
            return Response(
                {
                    'code': 'demo_lease_expired',
                    'detail': EXPIRED_EN,
                    'message_en': EXPIRED_EN,
                    'message_ar': EXPIRED_AR,
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(payload, status=status.HTTP_201_CREATED)
