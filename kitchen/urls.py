from django.urls import path

from .views import kitchen_orders_view

urlpatterns = [path("orders/", kitchen_orders_view, name="kitchen-orders")]
