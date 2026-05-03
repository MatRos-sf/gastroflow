from django.urls import path

import order.views.bill_views as bill_view
import order.views.order_views as order_view
import order.views.report_views as report_view

# TODO: name app "order"

url_report_pattern = [
    path("report/", report_view.ReportDispatchView.as_view(), name="report"),
    path("report/generate/", report_view.generate_report_view, name="report-generate"),
]

urlpatterns = [
    path("bill/", bill_view.BillListView.as_view(), name="list-bill"),
    path("bill/<int:pk>/", bill_view.BillDetailView.as_view(), name="detail-bill"),
    path(
        "bill/<int:pk>/delete/", bill_view.BillDeleteView.as_view(), name="delete-bill"
    ),
    path("bill/<int:pk>/edit/", bill_view.edit_bill, name="edit-bill"),
    path("bill/<int:pk>/close/", bill_view.close_bill, name="close-bill"),
    path("bill/<int:pk>/discount/", bill_view.add_discount, name="add-discount"),
    path(
        "bill/<int:pk>/close-with-release/",
        bill_view.close_bill_with_release,
        name="bill-close-release",
    ),
    path("<int:pk>/delete/", order_view.delete_order, name="delete-order"),
    path(
        "item/<int:pk_item>/delete/",
        order_view.delete_ordered_item,
        name="delete-order-item",
    ),
    path("ready/", order_view.ReadyOrderListView.as_view(), name="ready-order-list"),
] + url_report_pattern
