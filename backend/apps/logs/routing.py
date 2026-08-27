from django.urls import path

from .consumers import ScraperLogConsumer

websocket_urlpatterns = [
    path("ws/logs", ScraperLogConsumer.as_asgi(), name="scraper-logs"),
    path("ws/logs/", ScraperLogConsumer.as_asgi(), name="scraper-logs-slash"),
]
