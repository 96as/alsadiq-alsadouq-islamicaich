from django.urls import path
from . import views

app_name = 'content_safety'

urlpatterns = [
    path('alerts/', views.AlertListView.as_view(), name='alert_list'),
    path('alerts/<int:alert_id>/read/', views.AlertMarkReadView.as_view(), name='alert_mark_read'),
]
