from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ParentProfile, ChildProfile, ParentChildLink, Avatar


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_parent', 'is_child', 'is_staff', 'is_active')
    list_filter = ('is_parent', 'is_child', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Flags', {'fields': ('is_parent', 'is_child')}),
    )


class AvatarInline(admin.TabularInline):
    model = Avatar
    extra = 0


class ChildBadgeInline(admin.TabularInline):
    model = ParentChildLink
    fk_name = 'child'
    extra = 0


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'phone', 'birth_year', 'created_at')
    list_filter = ('birth_year',)
    search_fields = ('name', 'user__username', 'phone')


class ParentChildLinkInline(admin.TabularInline):
    model = ParentChildLink
    fk_name = 'child'
    extra = 0


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'user', 'gender', 'birth_year', 'avatar_visible', 'created_at')
    list_filter = ('gender', 'avatar_visible')
    search_fields = ('nickname', 'user__username')
    inlines = [ParentChildLinkInline, AvatarInline]


@admin.register(ParentChildLink)
class ParentChildLinkAdmin(admin.ModelAdmin):
    list_display = ('parent', 'child', 'consent_status', 'date_linked')
    list_filter = ('consent_status',)
    search_fields = ('parent__name', 'child__nickname')


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    list_display = ('child', 'emotion_state', 'lip_sync_status')
    list_filter = ('emotion_state', 'lip_sync_status')
    search_fields = ('child__nickname',)