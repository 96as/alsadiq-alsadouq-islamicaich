"""
Superadmin URL configuration.

- /superadmin/           → Dashboard SPA (template view)
- /superadmin/api/...    → read-only REST API endpoints
"""
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from superadmin import views

app_name = 'superadmin'

router = DefaultRouter()

# Authentication
router.register('users', views.UserViewSet, basename='users')
router.register('parent-profiles', views.ParentProfileViewSet, basename='parent-profiles')
router.register('child-profiles', views.ChildProfileViewSet, basename='child-profiles')
router.register('parent-child-links', views.ParentChildLinkViewSet, basename='parent-child-links')
router.register('avatars', views.AvatarViewSet, basename='avatars')

# Conversation
router.register('sessions', views.SessionViewSet, basename='sessions')
router.register('messages', views.MessageViewSet, basename='messages')

# Session Moral Context
router.register('moral-themes', views.MoralThemeViewSet, basename='moral-themes')
router.register('islamic-references', views.IslamicReferenceViewSet, basename='islamic-references')
router.register('moral-contexts', views.MoralContextViewSet, basename='moral-contexts')

# Content Safety
router.register('safety-flags', views.SafetyFlagViewSet, basename='safety-flags')
router.register('alerts', views.AlertViewSet, basename='alerts')

# Reporting
router.register('session-reports', views.SessionReportViewSet, basename='session-reports')
router.register(
    'child-session-memories', views.ChildSessionMemoryViewSet, basename='child-session-memories'
)
router.register('weekly-summaries', views.WeeklySummaryViewSet, basename='weekly-summaries')

# Gamification
router.register('levels', views.LevelViewSet, basename='levels')
router.register('points', views.PointsViewSet, basename='points')
router.register('badges', views.BadgeViewSet, basename='badges')
router.register('child-badges', views.ChildBadgeViewSet, basename='child-badges')
router.register('quests', views.QuestViewSet, basename='quests')
router.register('quest-progress', views.ChildQuestProgressViewSet, basename='quest-progress')

# Dashboard stats
router.register('stats', views.DashboardStatsViewSet, basename='stats')

urlpatterns = [
    # API routes
    path('api/', include(router.urls)),

    # Dashboard SPA — catch-all serves the single template
    path('', TemplateView.as_view(template_name='superadmin/dashboard.html'), name='dashboard'),
]
