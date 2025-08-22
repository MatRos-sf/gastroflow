"""
ASGI config for gastroflow project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gastroflow.settings")

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter


import bar.routing
import kitchen.routing
import service.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gastroflow.settings")




application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                kitchen.routing.websocket_urlpatterns
                + bar.routing.websocket_urlpatterns
                + service.routing.websocket_urlpatterns
            )
        ),
    }
)
