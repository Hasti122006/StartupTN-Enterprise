import asyncio

import redis.asyncio as redis
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings


class ScraperLogConsumer(AsyncWebsocketConsumer):
    """Streams Redis scraper logs for one job without exposing secrets."""

    async def connect(self):
        raw_job_id = self.scope["query_string"].decode().split("job_id=")[-1].split("&")[0]
        try:
            self.job_id = int(raw_job_id)
        except ValueError:
            await self.close(code=4400)
            return
        await self.accept()
        self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe(f"scraper:logs:{self.job_id}")
        self.listen_task = asyncio.create_task(self._stream())

    async def _stream(self):
        try:
            async for message in self.pubsub.listen():
                if message.get("type") == "message":
                    await self.send(text_data=message["data"])
        except Exception:
            await self.close(code=1011)

    async def disconnect(self, close_code):
        if hasattr(self, "listen_task"):
            self.listen_task.cancel()
        if hasattr(self, "pubsub"):
            await self.pubsub.unsubscribe(f"scraper:logs:{self.job_id}")
            await self.pubsub.aclose()
        if hasattr(self, "redis"):
            await self.redis.aclose()
