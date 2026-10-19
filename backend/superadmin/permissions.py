"""
Superadmin permissions — restrict all endpoints to superusers only.
"""
from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Allow access only to authenticated superusers."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )
