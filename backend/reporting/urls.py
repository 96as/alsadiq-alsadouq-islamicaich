from django.urls import path
from . import views

app_name = 'reporting'

urlpatterns = [
    path('insights/<int:child_id>/', views.ChildInsightsView.as_view(), name='child_insights'),
    path(
        'dashboard/<int:child_id>/',
        views.ChildActivityDashboardView.as_view(),
        name='child_dashboard',
    ),
]
