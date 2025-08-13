from django.urls import path

from . import views

app_name = "service"  # dodajemy namespace!

urlpatterns = [
    path("", views.menu_waiter, name="menu-waiter"),
    path("items/", views.item_list, name="items-waiter"),
    path("api/add-to-cart/", views.add_to_cart, name="add-to-cart"),
    path("cart/", views.cart, name="cart-waiter"),
    path(
        "api/remove-from-cart/<int:index>/",
        views.api_remove_from_cart,
        name="remove-from-cart",
    ),
    path("cart/summary/", views.do_order, name="summary-waiter"),
    path("clear-cart/", views.clear_cart, name="clear-cart"),
    path("bill/", views.BillListView.as_view(), name="bill"),
    path("bill/<int:pk>/", views.BillDetailView.as_view(), name="bill-detail"),
    path("bill/<int:pk>/close/", views.close_bill, name="close-bill"),
    path("order/table", views.tables_view, name="order-table"),
    path("order/table/settle", views.table_settle_view, name="table-settle"),
]
