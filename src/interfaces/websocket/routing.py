"""
WebSocket URL Routing
"""
from django.urls import re_path
from .consumers import AnimalRecognitionConsumer

websocket_urlpatterns = [
    re_path(r'ws/recognition/$', AnimalRecognitionConsumer.as_asgi()),
]
