from django.urls import path

from .views import (
    BillDeleteView,
    BillDetailView,
    BillListView,
    ExtendBillDetailView,
    OpenBillListView,
    ReadyOrderListView,
    close_bill,
    daily_report,
    delete_order_item,
    update_discount,
)

# TODO: name app "order"

urlpatterns = [
    path("", daily_report, name="daily-report"),
    path("update/discount/<int:pk>", update_discount, name="update-discount"),
    path("summary", BillListView.as_view(), name="summary-bill"),
    path("<int:pk>/delete/", BillDeleteView.as_view(), name="bill-delete"),
    path("<int:pk>/detail", BillDetailView.as_view(), name="bill-detail"),
    path("<int:pk>/extend", ExtendBillDetailView.as_view(), name="extend-bill-detail"),
    path(
        "<int:pk_order>/delete/<int:pk_item>",
        delete_order_item,
        name="delete-order-item",
    ),
    path("ready/", ReadyOrderListView.as_view(), name="ready-order-list"),
    path("bill/open/", OpenBillListView.as_view(), name="open-bill-list"),
    path("bill/<int:pk>/close/", close_bill, name="close-bill"),
]
