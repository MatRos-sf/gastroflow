from django.urls import path

from .views import kitchen_orders_view, HistoryOrderKitchen

urlpatterns = [
    path("orders/", kitchen_orders_view, name="kitchen-orders"),
    path("history/", HistoryOrderKitchen.as_view(), name="orders-history"),

]
