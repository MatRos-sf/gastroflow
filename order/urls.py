from django.urls import path

from .views import (
    BillDeleteView,
    BillDetailView,
    BillListView,
    ReadyOrderListView,
    daily_report,
    delete_order_item,
    update_discount,
)

urlpatterns = [
    path("", daily_report, name="daily-report"),
    path("update/discount/<int:pk>", update_discount, name="update-discount"),
    path("summary", BillListView.as_view(), name="summary-bill"),
    path("<int:pk>/delete/", BillDeleteView.as_view(), name="bill-delete"),
    path("<int:pk>/detail", BillDetailView.as_view(), name="bill-detail"),
    path(
        "<int:pk_order>/delete/<int:pk_item>",
        delete_order_item,
        name="delete-order-item",
    ),
    path("ready/", ReadyOrderListView.as_view(), name="ready-order-list"),
]
