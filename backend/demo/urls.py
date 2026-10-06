from django.urls import path

from .views import DemoResetView, DemoStartView

app_name = 'demo'

urlpatterns = [
    path('start', DemoStartView.as_view(), name='start'),
    path('start/', DemoStartView.as_view()),
    path('reset', DemoResetView.as_view(), name='reset'),
    path('reset/', DemoResetView.as_view()),
]
