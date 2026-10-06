"""Parent-facing alerts API views."""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import ParentChildLink
from authentication.permissions import IsParent
from conversation.models import QUIET_AUDIT_MODE, TurnAudit

from .models import NEUTRAL_ALERT_DESCRIPTION, NO_PARENT_NOTIFY_PREFIX, Alert, SafetyFlag


def _alerts_for(parent):
    """The parent's alerts, only for children whose link is still approved."""
    linked = ParentChildLink.objects.filter(
        parent=parent, consent_status='approved',
    ).values('child_id')
    return Alert.objects.filter(parent=parent, session__child_id__in=linked)


class AlertListView(APIView):
    """GET /api/alerts/ — safety/critical alerts for the authenticated parent."""
    permission_classes = [IsAuthenticated, IsParent]

    def get(self, request):
        parent = request.user.parent_profile
        qs = (
            _alerts_for(parent)
            .filter(alert_type='safety')
            .select_related('session', 'session__child')
            .order_by('-created_at')
        )
        session_ids = [a.session_id for a in qs]
        quiet_sessions = set(
            SafetyFlag.objects
            .filter(
                message__session__in=session_ids,
                description__startswith=NO_PARENT_NOTIFY_PREFIX,
            )
            .values_list('message__session_id', flat=True)
        ) | set(
            # the guard's own marker, written even when the flag was skipped or failed
            TurnAudit.objects
            .filter(session_id__in=session_ids, mode=QUIET_AUDIT_MODE)
            .values_list('session_id', flat=True)
        )
        data = [
            {
                'id': a.id,
                'alert_type': a.alert_type,
                'description': (
                    NEUTRAL_ALERT_DESCRIPTION
                    if a.description.startswith(NO_PARENT_NOTIFY_PREFIX)
                    or a.session_id in quiet_sessions
                    else a.description
                ),
                'is_read': a.is_read,
                'created_at': a.created_at.isoformat(),
                'session_id': a.session_id,
                'child_nickname': a.session.child.nickname if a.session and a.session.child else '',
            }
            for a in qs
        ]
        return Response(data)


class AlertMarkReadView(APIView):
    """PATCH /api/alerts/<id>/read/ — mark a single alert as read."""
    permission_classes = [IsAuthenticated, IsParent]

    def patch(self, request, alert_id):
        parent = request.user.parent_profile
        try:
            alert = _alerts_for(parent).get(pk=alert_id)
        except Alert.DoesNotExist:
            return Response(
                {'detail': 'Alert not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        alert.is_read = True
        alert.save(update_fields=['is_read'])
        return Response({'id': alert.id, 'is_read': True})
