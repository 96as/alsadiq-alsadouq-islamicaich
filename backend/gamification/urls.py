from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('quests/', views.QuestListView.as_view(), name='quest_list'),
    path('quests/<int:progress_id>/complete/', views.QuestCompleteView.as_view(), name='quest_complete'),
    path('badges/', views.BadgeListView.as_view(), name='badge_list'),
    path('level/', views.LevelView.as_view(), name='level'),
    path(
        'parent/children/<int:child_id>/quests/',
        views.ParentChildQuestListView.as_view(),
        name='parent_child_quests',
    ),
    path(
        'parent/quests/<int:progress_id>/verify/',
        views.ParentQuestVerifyView.as_view(),
        name='parent_quest_verify',
    ),
]
