from django.urls import re_path

from consumers import consumers

websocket_urlpatterns = [
    re_path(r"ws/bar/orders/", consumers.BarOrderConsumer.as_asgi()),
    re_path(r"ws/kitchen/orders/", consumers.OrderConsumer.as_asgi()),
]
