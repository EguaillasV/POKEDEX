"""WebSocket Package"""
from .consumers import AnimalRecognitionConsumer
from .routing import websocket_urlpatterns

__all__ = ['AnimalRecognitionConsumer', 'websocket_urlpatterns']
