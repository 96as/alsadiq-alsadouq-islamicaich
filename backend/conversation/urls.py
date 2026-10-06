from django.urls import path

from .views import (
    EndSessionView,
    LiveKitWebhookView,
    ParentChildConversationSummaryView,
    SessionMessagesView,
    StartSessionView,
)

app_name = 'conversation'

urlpatterns = [
    path(
        'parent/children/<int:child_id>/summary/',
        ParentChildConversationSummaryView.as_view(),
        name='parent_child_summary',
    ),
    path('sessions/', StartSessionView.as_view(), name='start_session'),
    path('sessions/<int:session_id>/end/', EndSessionView.as_view(), name='end_session'),
    path('sessions/<int:session_id>/messages/', SessionMessagesView.as_view(), name='session_messages'),
    path('webhook/', LiveKitWebhookView.as_view(), name='livekit_webhook'),
]
