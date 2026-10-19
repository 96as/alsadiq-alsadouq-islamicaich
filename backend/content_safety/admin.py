from django.contrib import admin
from .models import SafetyFlag, Alert


@admin.register(SafetyFlag)
class SafetyFlagAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'flag_type', 'is_blocked', 'flagged_at')
    list_filter = ('flag_type', 'is_blocked')
    search_fields = ('description', 'message__content')


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'parent', 'alert_type', 'is_read', 'created_at')
    list_filter = ('alert_type', 'is_read')
    search_fields = ('description', 'parent__name')