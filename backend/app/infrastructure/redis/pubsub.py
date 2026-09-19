"""Redis PubSub event broadcaster and consumer for real-time SSE progress."""

import json
from collections.abc import AsyncGenerator
from typing import Any

from app.core.logging import logger
from app.infrastructure.redis.client import get_redis_client


class EventBroadcaster:
    @staticmethod
    def get_channel_name(job_id: str) -> str:
        return f"job_events:{job_id}"

    @classmethod
    async def publish_event(
        cls,
        job_id: str,
        stage: str,
        progress: float,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "job_id": job_id,
            "stage": stage,
            "progress": round(progress, 1),
            "message": message,
            "data": data or {},
        }
        try:
            client = get_redis_client()
            await client.publish(cls.get_channel_name(job_id), json.dumps(payload))
        except Exception as e:
            logger.warning(f"Could not publish event to Redis: {e}")

    @classmethod
    async def subscribe_events(cls, job_id: str) -> AsyncGenerator[str, None]:
        client = get_redis_client()
        pubsub = client.pubsub()
        channel = cls.get_channel_name(job_id)
        await pubsub.subscribe(channel)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    yield f"data: {data}\n\n"
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
