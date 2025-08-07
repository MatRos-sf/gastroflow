# kitchen/routing.py
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/kitchen/orders/", consumers.OrderConsumer.as_asgi()),
]
