from django.urls import path

from .views import (
    BillDeleteView,
    BillDetailView,
    BillListView,
    daily_report,
    update_discount,
)

urlpatterns = [
    path("", daily_report, name="daily-report"),
    path("update/discount/<int:pk>", update_discount, name="update-discount"),
    path("summary", BillListView.as_view(), name="summary-bill"),
    path("<int:pk>/delete/", BillDeleteView.as_view(), name="bill-delete"),
    path("<int:pk>/detail", BillDetailView.as_view(), name="bill-detail"),
]
