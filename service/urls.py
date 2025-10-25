from django.urls import path

from . import views

app_name = "service"

urlpatterns = [
    path("", views.menu_waiter, name="menu-waiter"),
    path("items/", views.MenuWaiterView.as_view(), name="items-waiter"),
    path("cart/add/", views.CartAddView.as_view(), name="cart-add"),
    path("cart/", views.CardView.as_view(), name="cart"),
    path(
        "api/remove-from-cart/<int:index>/",
        views.api_remove_from_cart,
        name="remove-from-cart",
    ),
    path("cart/clear", views.clear_cart, name="cart-clear"),
    path("bill/", views.BillListView.as_view(), name="bill"),
    path("bill/<int:pk>/", views.BillDetailView.as_view(), name="bill-detail"),
    path("bill/<int:pk>/close/", views.close_bill, name="close-bill"),
    path("order/table", views.tables_view, name="order-table"),
    path("order/table/settle", views.table_settle_view, name="table-settle"),
    path(
        "service/notifications/", views.waiter_notification, name="waiter-notifications"
    ),
    path(
        "order/table/settle/bill/<int:pk>",
        views.add_order_to_bill,
        name="table-settle-add-order",
    ),
    path(
        "api/notifications/check/",
        views.check_notifications,
        name="check-notifications",
    ),
]
