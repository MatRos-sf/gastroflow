from django.urls import path

from .views import bar_orders

urlpatterns = [
    path("orders/", bar_orders, name="bar-orders"),
]
