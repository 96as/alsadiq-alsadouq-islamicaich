"""
Superadmin API views — read-only ViewSets for every model (edits belong in Django /admin).
All views are restricted to superusers via IsSuperAdmin permission.
"""
from rest_framework import viewsets
from rest_framework.response import Response

from superadmin.permissions import IsSuperAdmin
from superadmin.serializers import (
    UserSerializer, ParentProfileSerializer, ChildProfileSerializer,
    ParentChildLinkSerializer, AvatarSerializer,
    SessionSerializer, MessageSerializer,
    MoralThemeSerializer, IslamicReferenceSerializer, MoralContextSerializer,
    SafetyFlagSerializer, AlertSerializer,
    SessionReportSerializer, WeeklySummarySerializer, ChildSessionMemorySerializer,
    LevelSerializer, PointsSerializer, BadgeSerializer,
    ChildBadgeSerializer, QuestSerializer, ChildQuestProgressSerializer,
)
from authentication.models import (
    User, ParentProfile, ChildProfile, ParentChildLink, Avatar,
)
from conversation.models import Session, Message
from session_moral_context.models import MoralTheme, IslamicReference, MoralContext
from content_safety.models import SafetyFlag, Alert
from reporting.models import ChildSessionMemory, SessionReport, WeeklySummary
from gamification.models import (
    Level, Points, Badge, ChildBadge, Quest, ChildQuestProgress,
)


class SuperAdminMixin:
    """Common config for all superadmin viewsets."""
    permission_classes = [IsSuperAdmin]


# ============================================
# Authentication
# ============================================

class UserViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class ParentProfileViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ParentProfile.objects.select_related('user').all().order_by('-created_at')
    serializer_class = ParentProfileSerializer


class ChildProfileViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ChildProfile.objects.select_related('user').all().order_by('-created_at')
    serializer_class = ChildProfileSerializer


class ParentChildLinkViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ParentChildLink.objects.select_related('parent', 'child').all().order_by('-date_linked')
    serializer_class = ParentChildLinkSerializer


class AvatarViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Avatar.objects.select_related('child').all()
    serializer_class = AvatarSerializer


# ============================================
# Conversation
# ============================================

class SessionViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Session.objects.select_related('child').all().order_by('-started_at')
    serializer_class = SessionSerializer


class MessageViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Message.objects.select_related('session').all().order_by('-created_at')
    serializer_class = MessageSerializer


# ============================================
# Session Moral Context
# ============================================

class MoralThemeViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = MoralTheme.objects.all().order_by('name')
    serializer_class = MoralThemeSerializer


class IslamicReferenceViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = IslamicReference.objects.all().order_by('reference_type', 'text')
    serializer_class = IslamicReferenceSerializer


class MoralContextViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = MoralContext.objects.prefetch_related('themes', 'references').all()
    serializer_class = MoralContextSerializer


# ============================================
# Content Safety
# ============================================

class SafetyFlagViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = SafetyFlag.objects.select_related('message').all().order_by('-flagged_at')
    serializer_class = SafetyFlagSerializer


class AlertViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Alert.objects.select_related('session', 'parent').all().order_by('-created_at')
    serializer_class = AlertSerializer


# ============================================
# Reporting
# ============================================

class SessionReportViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = SessionReport.objects.select_related('session').all().order_by('-created_at')
    serializer_class = SessionReportSerializer


class ChildSessionMemoryViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ChildSessionMemory.objects.select_related('child').all().order_by('-updated_at')
    serializer_class = ChildSessionMemorySerializer


class WeeklySummaryViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = WeeklySummary.objects.select_related('child', 'parent').prefetch_related('sessions').all().order_by('-week_start')
    serializer_class = WeeklySummarySerializer


# ============================================
# Gamification
# ============================================

class LevelViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Level.objects.all().order_by('number')
    serializer_class = LevelSerializer


class PointsViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Points.objects.select_related('child').all()
    serializer_class = PointsSerializer


class BadgeViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Badge.objects.all().order_by('name')
    serializer_class = BadgeSerializer


class ChildBadgeViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ChildBadge.objects.select_related('child', 'badge').all().order_by('-earned_at')
    serializer_class = ChildBadgeSerializer


class QuestViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Quest.objects.select_related('moral_theme', 'session_report').all()
    serializer_class = QuestSerializer


class ChildQuestProgressViewSet(SuperAdminMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ChildQuestProgress.objects.select_related('child', 'quest').all()
    serializer_class = ChildQuestProgressSerializer


# ============================================
# Dashboard Stats (read-only)
# ============================================

class DashboardStatsViewSet(viewsets.ViewSet):
    """Aggregated stats for the dashboard overview."""
    permission_classes = [IsSuperAdmin]

    def list(self, request):
        return Response({
            'users': User.objects.count(),
            'parents': ParentProfile.objects.count(),
            'children': ChildProfile.objects.count(),
            'sessions': Session.objects.count(),
            'messages': Message.objects.count(),
            'safety_flags': SafetyFlag.objects.count(),
            'alerts': Alert.objects.count(),
            'alerts_unread': Alert.objects.filter(is_read=False).count(),
            'session_reports': SessionReport.objects.count(),
            'weekly_summaries': WeeklySummary.objects.count(),
            'child_session_memories': ChildSessionMemory.objects.count(),
            'ai_generated_quests': Quest.objects.filter(is_ai_generated=True).count(),
        })
