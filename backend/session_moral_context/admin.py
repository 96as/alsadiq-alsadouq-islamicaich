from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    MoralTheme, IslamicReference, MoralContext,
    Value, ContentItem, ValueItem, ServedReference,
)


class LegacyReadOnlyAdmin(admin.ModelAdmin):
    """Legacy, pre-bank (r5 A1). Read-only. Retired with Quest.value (r6 G3)"""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MoralTheme)
class MoralThemeAdmin(LegacyReadOnlyAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)


@admin.register(IslamicReference)
class IslamicReferenceAdmin(LegacyReadOnlyAdmin):
    list_display = ('id', 'reference_type', 'short_text', 'source', 'is_verified')
    list_filter = ('reference_type', 'is_verified', 'themes')
    search_fields = ('text', 'source')
    filter_horizontal = ('themes',)

    def short_text(self, obj):
        return obj.text[:80]
    short_text.short_description = 'Text'


@admin.register(MoralContext)
class MoralContextAdmin(LegacyReadOnlyAdmin):
    list_display = ('id', 'message', 'story_source')
    search_fields = ('story_source', 'message__content')
    filter_horizontal = ('themes', 'references')


@admin.register(Value)
class ValueAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name_ar', 'name_en', 'order')
    search_fields = ('slug', 'name_ar', 'name_en')
    ordering = ('order',)


class ValueItemInline(admin.TabularInline):
    model = ValueItem
    extra = 1


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'short_text', 'surah', 'ayah', 'book', 'number',
                    'content_level', 'verification_status')
    list_filter = ('type', 'content_level', 'verification_status', 'values', 'source_site')
    search_fields = ('search_text_norm',)
    filter_horizontal = ('related',)
    inlines = [ValueItemInline]
    readonly_fields = ('reviewed_by', 'reviewed_at', 'search_text_norm')
    actions = ['mark_reviewed']

    def short_text(self, obj):
        return (obj.english_text or obj.arabic_text)[:80]
    short_text.short_description = 'Text'

    def save_model(self, request, obj, form, change):
        if obj.verification_status == 'reviewed':
            if not change or form.changed_data:
                obj.reviewed_by, obj.reviewed_at = request.user, timezone.now()
        else:
            obj.reviewed_by = obj.reviewed_at = None
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.save()  # refresh search_text_norm with inline value keywords

    @admin.action(description='Mark reviewed')
    def mark_reviewed(self, request, queryset):
        ok, failed = 0, []
        for item in queryset:
            item.verification_status = 'reviewed'
            item.reviewed_by = request.user
            item.reviewed_at = timezone.now()
            try:
                item.full_clean()
            except ValidationError as e:
                failed.append(f'{item.pk}: {"; ".join(e.messages)}')
                continue
            item.save()
            ok += 1
        self.message_user(request, f'{ok} item(s) marked reviewed.')
        for f in failed:
            self.message_user(request, f'Not reviewed - {f}', level='error')


@admin.register(ServedReference)
class ServedReferenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'item', 'via', 'served_at')
    list_filter = ('via',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
