from django.urls import path

import order._views.bill_views as _views
import order._views.order_views as _views_order
import order._views.report_views as _views_report

from .views import ReadyOrderListView, generate_report

# TODO: name app "order"

url_report_pattern = [
    path("report/", _views_report.ReportDispatchView.as_view(), name="report"),
    path("report/generate/<str:from_to>/", generate_report, name="report-generate"),
]

urlpatterns = [
    path("bill/", _views.BillListView.as_view(), name="list-bill"),
    path("bill/<int:pk>/", _views.BillDetailView.as_view(), name="detail-bill"),
    path("bill/<int:pk>/delete/", _views.BillDeleteView.as_view(), name="delete-bill"),
    path("bill/<int:pk>/edit/", _views.edit_bill, name="edit-bill"),
    path("bill/<int:pk>/close/", _views.close_bill, name="close-bill"),
    path("bill/<int:pk>/discount/", _views.add_discount, name="add-discount"),
    path(
        "bill/<int:pk>/close-with-release/",
        _views.close_bill_with_release,
        name="bill-close-release",
    ),
    path("<int:pk>/delete/", _views_order.delete_order, name="delete-order"),
    path(
        "item/<int:pk_item>/delete/",
        _views_order.delete_ordered_item,
        name="delete-order-item",
    ),
    path("ready/", ReadyOrderListView.as_view(), name="ready-order-list"),
] + url_report_pattern
