"""Child-facing gamification serializers."""
from rest_framework import serializers

from .models import Badge, ChildBadge, ChildQuestProgress, Level, Points, Quest


class ChildQuestSerializer(serializers.ModelSerializer):
    """Quest progress row as seen by the child."""
    quest_id = serializers.IntegerField(source='quest.id', read_only=True)
    title = serializers.CharField(source='quest.title', read_only=True)
    description = serializers.CharField(source='quest.description', read_only=True)
    reward_points = serializers.IntegerField(source='quest.reward_points', read_only=True)
    quest_type = serializers.CharField(source='quest.quest_type', read_only=True)
    verification_method = serializers.CharField(
        source='quest.verification_method', read_only=True
    )
    moral_theme_name = serializers.SerializerMethodField()
    value_slug = serializers.CharField(source='quest.value.slug', read_only=True, default=None)
    value_name_en = serializers.CharField(source='quest.value.name_en', read_only=True, default=None)
    value_name_ar = serializers.CharField(source='quest.value.name_ar', read_only=True, default=None)
    is_ai_generated = serializers.BooleanField(source='quest.is_ai_generated', read_only=True)

    class Meta:
        model = ChildQuestProgress
        fields = [
            'id', 'quest_id', 'title', 'description', 'reward_points',
            'quest_type', 'verification_method', 'moral_theme_name',
            'value_slug', 'value_name_en', 'value_name_ar',
            'status', 'started_at', 'completed_at', 'proof_note',
            'verified_by', 'is_ai_generated',
        ]
        read_only_fields = fields

    def get_moral_theme_name(self, obj):
        mt = obj.quest.moral_theme
        return mt.name if mt else None


class ChildBadgeSerializer(serializers.ModelSerializer):
    """Badge definition with earned status for the requesting child."""
    earned = serializers.BooleanField(read_only=True)
    earned_at = serializers.DateTimeField(read_only=True, allow_null=True)
    progress_current = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'description', 'icon', 'category',
            'requirement_type', 'requirement_value',
            'earned', 'earned_at', 'progress_current',
        ]
        read_only_fields = fields


class ChildLevelSerializer(serializers.Serializer):
    level_name = serializers.CharField()
    level_number = serializers.IntegerField()
    total_points = serializers.IntegerField()
    current_level_min = serializers.IntegerField()
    next_level_min = serializers.IntegerField(allow_null=True)
    progress_pct = serializers.IntegerField()
    current_streak = serializers.IntegerField(required=False, default=0)
