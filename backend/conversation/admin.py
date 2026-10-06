from django.contrib import admin
from .models import Session, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'child', 'mood_state', 'started_at', 'ended_at', 'duration')
    list_filter = ('mood_state', 'started_at')
    search_fields = ('child__nickname', 'child__user__username')
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'sender', 'input_type', 'language', 'short_content', 'created_at')
    list_filter = ('sender', 'input_type', 'language')
    search_fields = ('content',)

    def short_content(self, obj):
        return obj.content[:80]
    short_content.short_description = 'Content'