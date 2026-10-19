from rest_framework.permissions import BasePermission


class IsParent(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_parent
        )


class IsChild(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_child
        )


class IsLinkedParent(BasePermission):
    """Object-level: ensures parent has an approved link to the child."""

    def has_object_permission(self, request, view, obj):
        from .models import ParentChildLink

        if not request.user.is_parent:
            return False
        child = getattr(obj, 'child', obj)
        return ParentChildLink.objects.filter(
            parent=request.user.parent_profile,
            child=child,
            consent_status='approved',
        ).exists()
