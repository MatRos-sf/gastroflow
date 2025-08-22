from django.urls import path

from .views import BarOrderKitchen, bar_orders

urlpatterns = [
    path("orders/", bar_orders, name="bar-orders"),
    path("history/", BarOrderKitchen.as_view(), name="orders-bar-history"),
]
