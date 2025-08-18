from django.urls import path

from .views import daily_report

urlpatterns = [
    path("", daily_report, name="daily-report"),
]
