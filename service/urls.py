from django.urls import path

from .views.action import ActionBillListView
from .views.order_flow.cart import CartSummaryView
from .views.order_flow.menu import MenuWaiterView
from .views.order_flow.table_select import table_select_view
from .views.service import (
    CartAddView,
    clear_cart,
    main_menu_view,
    remove_item_from_cart,
    select_existing_bill,
    unread_notifications_api,
)
from .views.table_view import (
    HallCreateView,
    HallFloorEditorView,
    HallListView,
    HallUpdateView,
    change_table,
    hall_floor_editor_save,
)

app_name = "service"

api_urlpatterns = [
    path(
        "api/remove-from-cart/<int:index>/",
        remove_item_from_cart,
        name="remove-from-cart",
    ),
    path(
        "api/notifications/check/",
        unread_notifications_api,
        name="check-notifications",
    ),
]

urlpatterns = [
    path("", main_menu_view, name="main-menu"),
    path("order/select/table", table_select_view, name="order-select-table"),
    path("order/select/items", MenuWaiterView.as_view(), name="order-select-items"),
    path("order/cart/summary/", CartSummaryView.as_view(), name="order-cart-summary"),
    path("service/cart/add/", CartAddView.as_view(), name="cart-add-item"),
    path(
        "service/bill/<int:pk>/add-order/",
        select_existing_bill,
        name="bill-add-order",
    ),
    path(
        "action/<str:action>/<int:table>/",
        ActionBillListView.as_view(),
        name="open-bill-list",
    ),
    path("cart/clear", clear_cart, name="cart-clear"),
    path("bill/<int:pk>/change-table/", change_table, name="change-table"),
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
] + api_urlpatterns
