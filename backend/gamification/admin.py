from django.contrib import admin
from .models import (
    Badge,
    ChildBadge,
    ChildQuestProgress,
    ChildStreak,
    Level,
    Points,
    PointsEvent,
    Quest,
)


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'required_points')
    ordering = ('number',)


@admin.register(Points)
class PointsAdmin(admin.ModelAdmin):
    list_display = ('child', 'total', 'current_level')
    search_fields = ('child__nickname',)


class ChildBadgeInline(admin.TabularInline):
    model = ChildBadge
    extra = 0


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'category', 'requirement_type',
        'requirement_value', 'sort_order',
    )
    list_filter = ('category', 'requirement_type')
    search_fields = ('name',)
    inlines = [ChildBadgeInline]


@admin.register(PointsEvent)
class PointsEventAdmin(admin.ModelAdmin):
    list_display = ('child', 'delta', 'source', 'reason', 'session', 'created_at')
    list_filter = ('source',)
    search_fields = ('child__nickname', 'reason')
    date_hierarchy = 'created_at'


@admin.register(ChildStreak)
class ChildStreakAdmin(admin.ModelAdmin):
    list_display = ('child', 'current_streak', 'longest_streak', 'last_active_date')
    search_fields = ('child__nickname',)


@admin.register(ChildBadge)
class ChildBadgeAdmin(admin.ModelAdmin):
    list_display = ('child', 'badge', 'earned_at')
    list_filter = ('badge',)
    search_fields = ('child__nickname', 'badge__name')


class ChildQuestProgressInline(admin.TabularInline):
    model = ChildQuestProgress
    extra = 0


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'quest_type',
        'verification_method',
        'reward_points',
        'moral_theme',
        'is_ai_generated',
        'session_report',
    )
    list_filter = ('quest_type', 'verification_method', 'moral_theme', 'is_ai_generated')
    search_fields = ('title',)
    inlines = [ChildQuestProgressInline]


@admin.register(ChildQuestProgress)
class ChildQuestProgressAdmin(admin.ModelAdmin):
    list_display = ('child', 'quest', 'status', 'started_at', 'completed_at')
    list_filter = ('status',)
    search_fields = ('child__nickname', 'quest__title')