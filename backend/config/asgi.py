"""
ASGI config — supports both HTTP and WebSocket protocols.

Reference: SYSTEM_ARCHITECTURE_AND_DESIGN.md §8.3
"""
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Initialize Django ASGI application early to populate AppRegistry
django_asgi_app = get_asgi_application()

# Import WebSocket URL patterns after Django setup
# from apps.review.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # Uncomment when WebSocket routes are defined:
        # "websocket": AllowedHostsOriginValidator(
        #     AuthMiddlewareStack(
        #         URLRouter(websocket_urlpatterns)
        #     )
        # ),
    }
)
