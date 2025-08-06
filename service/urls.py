from django.urls import path

from . import views

app_name = "service"  # dodajemy namespace!

urlpatterns = [
    path("", views.menu_waiter, name="menu-waiter"),
    path("items/", views.item_list, name="items-waiter"),
    path("api/add-to-cart/", views.add_to_cart, name="add-to-cart"),
    #     path("api/add-to-cart/", views.api_add_to_cart, name="add-to-cart"),  # ← używamy add-to-cart
    path("cart/", views.cart, name="cart-waiter"),
    path(
        "api/remove-from-cart/<int:index>/",
        views.api_remove_from_cart,
        name="remove-from-cart",
    ),
    path("cart/summary/", views.do_order, name="summary-waiter"),
    # path("api/remove-from-cart/", views.api_remove_from_cart, name="remove-from-cart"),
]
