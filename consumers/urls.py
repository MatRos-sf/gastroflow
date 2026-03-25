from django.urls import path

from consumers.views import bar_orders_view, kitchen_orders_view, notifications_view

app_name = "gf-display"

urlpatterns = [
    path("kitchen/orders/", kitchen_orders_view, name="kitchen-orders"),
    path("bar/orders/", bar_orders_view, name="bar-orders"),
    path("notifications/", notifications_view, name="waiter-notifications"),
]
