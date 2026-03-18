from django.urls import path

from . import views
from ._views.order_flow.cart import CartSummaryView
from ._views.order_flow.menu import MenuWaiterView
from ._views.order_flow.table_select import table_select_view
from ._views.table_view import (
    HallCreateView,
    HallFloorEditorView,
    HallListView,
    HallUpdateView,
    hall_floor_editor_save,
)

app_name = "service"

urlpatterns = [
    path("", views.menu_waiter, name="menu-waiter"),
    path("order/select/table", table_select_view, name="order-select-table"),
    path("order/select/items", MenuWaiterView.as_view(), name="order-select-items"),
    path("order/cart/summary/", CartSummaryView.as_view(), name="order-cart-summary"),
    path("cart/add/", views.CartAddView.as_view(), name="cart-add"),
    path(
        "api/remove-from-cart/<int:index>/",
        views.api_remove_from_cart,
        name="remove-from-cart",
    ),
    path("cart/clear", views.clear_cart, name="cart-clear"),
    path("order/table/settle", views.table_settle_view, name="table-settle"),
    path(
        "order/table/settle/bill/<int:pk>",
        views.add_order_to_bill,
        name="table-settle-add-order",
    ),
    path("bill/<int:pk>/change-table", views.change_table, name="change-table"),
    path(
        "service/notifications/", views.waiter_notification, name="waiter-notifications"
    ),
    path(
        "api/notifications/check/",
        views.check_notifications,
        name="check-notifications",
    ),
    path("halls/", HallListView.as_view(), name="hall-list"),
    path("halls/create/", HallCreateView.as_view(), name="hall-create"),
    path("halls/<int:pk>/update/", HallUpdateView.as_view(), name="hall-update"),
    path(
        "halls/<int:pk>/floor-editor/",
        HallFloorEditorView.as_view(),
        name="hall-floor-editor",
    ),
    path(
        "halls/<int:pk>/floor-editor/save/",
        hall_floor_editor_save,
        name="hall-floor-editor-save",
    ),
]
