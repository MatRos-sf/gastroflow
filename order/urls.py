from django.urls import path

import order._views.bill_views as _views

from .views import (
    ActionBillListView,
    BillDeleteView,
    ReadyOrderListView,
    ReportSelectionView,
    ReportView,
    close_bill,
    delete_order_item,
    generate_report,
    update_discount,
)

# TODO: name app "order"

url_report_pattern = [
    path("report", ReportView.as_view(), name="report"),
    path("report/generate/<str:from_to>/", generate_report, name="report-generate"),
    path("report-selection/", ReportSelectionView.as_view(), name="report-selection"),
]

urlpatterns = [
    path("bill/", _views.BillListView.as_view(), name="list-bill"),
    path("bill/<int:pk>/", _views.BillDetailView.as_view(), name="detail-bill"),
    path("update/discount/<int:pk>", update_discount, name="update-discount"),
    path("<int:pk>/delete/", BillDeleteView.as_view(), name="bill-delete"),
    path(
        "<int:pk_order>/delete/<int:pk_item>",
        delete_order_item,
        name="delete-order-item",
    ),
    path("ready/", ReadyOrderListView.as_view(), name="ready-order-list"),
    path(
        "action/<str:action>/<int:table>/",
        ActionBillListView.as_view(),
        name="open-bill-list",
    ),
    path("bill/<int:pk>/close/", close_bill, name="close-bill"),
] + url_report_pattern
