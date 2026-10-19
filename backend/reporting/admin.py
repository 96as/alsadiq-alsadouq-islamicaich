from django.contrib import admin

from .models import ChildSessionMemory, SessionReport, WeeklySummary
from .services import _value_choices, clean_values_to_revisit


@admin.register(SessionReport)
class SessionReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('insight_summary', 'recommendations')
    readonly_fields = ('values_to_revisit', 'raw_llm_output', 'created_at')
    fieldsets = (
        (None, {'fields': ('session', 'values_to_revisit', 'insight_summary', 'recommendations')}),
        ('LLM output', {'fields': ('raw_llm_output', 'created_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Values to revisit')
    def values_to_revisit(self, obj):
        raw = obj.raw_llm_output if obj else {}
        slugs = raw.get('values_to_revisit', []) if isinstance(raw, dict) else []
        return clean_values_to_revisit(slugs, _value_choices())


@admin.register(ChildSessionMemory)
class ChildSessionMemoryAdmin(admin.ModelAdmin):
    list_display = ("id", "child", "updated_at")
    search_fields = ("rolling_summary", "child__nickname")


@admin.register(WeeklySummary)
class WeeklySummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'child', 'parent', 'week_start', 'created_at')
    list_filter = ('week_start',)
    search_fields = ('summary', 'child__nickname', 'parent__name')
    filter_horizontal = ('sessions',)
