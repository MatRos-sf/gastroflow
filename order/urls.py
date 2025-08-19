from django.urls import path

from .views import daily_report, update_discount

urlpatterns = [
    path("", daily_report, name="daily-report"),
    path("update/discount/<int:pk>", update_discount, name="update-discount"),
]
