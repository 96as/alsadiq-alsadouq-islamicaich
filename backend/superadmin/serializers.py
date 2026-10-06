"""
Superadmin serializers — full CRUD serializers for every model.
Uses ModelSerializer for all models with explicit field declarations.
"""
from rest_framework import serializers

from authentication.models import (
    User, ParentProfile, ChildProfile, ParentChildLink, Avatar,
)
from conversation.models import Session, Message
from session_moral_context.models import MoralTheme, IslamicReference, MoralContext
from content_safety.models import SafetyFlag, Alert
from reporting.models import ChildSessionMemory, SessionReport, WeeklySummary
from reporting.services import _value_choices, clean_values_to_revisit
from gamification.models import (
    Level, Points, Badge, ChildBadge, Quest, ChildQuestProgress,
)


# ============================================
# Authentication
# ============================================

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_parent', 'is_child', 'is_staff', 'is_superuser',
            'is_active', 'date_joined', 'last_login',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user


class ParentProfileSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ParentProfile
        fields = ['id', 'user', 'user_username', 'name', 'phone', 'birth_year', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChildProfileSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ChildProfile
        fields = [
            'id', 'user', 'user_username', 'nickname', 'gender',
            'birth_year', 'avatar_visible', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ParentChildLinkSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    child_nickname = serializers.CharField(source='child.nickname', read_only=True)

    class Meta:
        model = ParentChildLink
        fields = [
            'id', 'parent', 'parent_name', 'child', 'child_nickname',
            'consent_status', 'date_linked', 'memory',
        ]
        read_only_fields = ['id', 'date_linked']


class AvatarSerializer(serializers.ModelSerializer):
    child_nickname = serializers.CharField(source='child.nickname', read_only=True)

    class Meta:
        model = Avatar
        fields = ['id', 'child', 'child_nickname', 'emotion_state', 'lip_sync_status']
        read_only_fields = ['id']


# ============================================
# Conversation
# ============================================

class SessionSerializer(serializers.ModelSerializer):
    child_nickname = serializers.CharField(source='child.nickname', read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = [
            'id', 'child', 'child_nickname', 'mood_state',
            'started_at', 'ended_at', 'duration',
        ]
        read_only_fields = ['id', 'started_at']

    def get_duration(self, obj):
        d = obj.duration
        if d:
            total = int(d.total_seconds())
            mins, secs = divmod(total, 60)
            return f"{mins}m {secs}s"
        return None


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            'id', 'session', 'sender', 'content', 'input_type',
            'language', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ============================================
# Session Moral Context
# ============================================

class MoralThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoralTheme
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class IslamicReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IslamicReference
        fields = ['id', 'reference_type', 'text', 'source']
        read_only_fields = ['id']


class MoralContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoralContext
        fields = ['id', 'message', 'themes', 'references', 'story_source']
        read_only_fields = ['id']


# ============================================
# Content Safety
# ============================================

class SafetyFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyFlag
        fields = ['id', 'message', 'flag_type', 'description', 'is_blocked', 'flagged_at']
        read_only_fields = ['id', 'flagged_at']


class AlertSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'session', 'parent', 'parent_name',
            'alert_type', 'description', 'is_read', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ============================================
# Reporting
# ============================================

class SessionReportSerializer(serializers.ModelSerializer):
    values_to_revisit = serializers.SerializerMethodField()

    def get_values_to_revisit(self, obj):
        raw = obj.raw_llm_output
        slugs = raw.get('values_to_revisit', []) if isinstance(raw, dict) else []
        return clean_values_to_revisit(slugs, _value_choices())

    class Meta:
        model = SessionReport
        fields = [
            'id', 'session', 'values_to_revisit', 'insight_summary',
            'recommendations', 'raw_llm_output', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'raw_llm_output', 'values_to_revisit']


class ChildSessionMemorySerializer(serializers.ModelSerializer):
    child_nickname = serializers.CharField(source='child.nickname', read_only=True)

    class Meta:
        model = ChildSessionMemory
        fields = [
            'id', 'child', 'child_nickname', 'rolling_summary', 'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']


class WeeklySummarySerializer(serializers.ModelSerializer):
    child_nickname = serializers.CharField(source='child.nickname', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    class Meta:
        model = WeeklySummary
        fields = [
            'id', 'child', 'child_nickname', 'parent', 'parent_name',
            'week_start', 'summary', 'sessions', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ============================================
# Gamification
# ============================================

class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['id', 'number', 'name', 'required_points']
        read_only_fields = ['id']


class PointsSerializer(serializers.ModelSerializer):
    child_nickname = serializers.CharField(source='child.nickname', read_only=True)
    current_level = serializers.SerializerMethodField()

    class Meta:
        model = Points
        fields = ['id', 'child', 'child_nickname', 'total', 'current_level']
        read_only_fields = ['id']

    def get_current_level(self, obj):
        level = obj.current_level
        return level.name if level else None


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['id', 'name', 'description', 'icon']
        read_only_fields = ['id']


class ChildBadgeSerializer(serializers.ModelSerializer):
    child_nickname = serializers.CharField(source='child.nickname', read_only=True)
    badge_name = serializers.CharField(source='badge.name', read_only=True)

    class Meta:
        model = ChildBadge
        fields = ['id', 'child', 'child_nickname', 'badge', 'badge_name', 'earned_at']
        read_only_fields = ['id', 'earned_at']


class QuestSerializer(serializers.ModelSerializer):
    moral_theme_name = serializers.CharField(source='moral_theme.name', read_only=True)

    class Meta:
        model = Quest
        fields = [
            'id', 'title', 'description', 'reward_points',
            'moral_theme', 'moral_theme_name',
            'session_report', 'is_ai_generated',
        ]
        read_only_fields = ['id']


class ChildQuestProgressSerializer(serializers.ModelSerializer):
    child_nickname = serializers.CharField(source='child.nickname', read_only=True)
    quest_title = serializers.CharField(source='quest.title', read_only=True)

    class Meta:
        model = ChildQuestProgress
        fields = [
            'id', 'child', 'child_nickname', 'quest', 'quest_title',
            'status', 'started_at', 'completed_at',
        ]
        read_only_fields = ['id']
