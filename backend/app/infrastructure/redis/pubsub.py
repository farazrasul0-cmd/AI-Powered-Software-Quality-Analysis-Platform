"""Redis PubSub event broadcaster and consumer for real-time SSE progress."""

import json
from collections.abc import AsyncGenerator
from typing import Any

from app.core.logging import logger
from app.infrastructure.redis.client import get_redis_client


class EventBroadcaster:
    _redis_online: bool | None = None
    _redis_check_time: float = 0.0

    @staticmethod
    def get_channel_name(job_id: str) -> str:
        return f"job_events:{job_id}"

    @classmethod
    def _is_redis_online(cls) -> bool:
        import socket, time
        from app.core.config import settings
        now = time.time()
        if cls._redis_online is not None and (now - cls._redis_check_time) < 30.0:
            return cls._redis_online
        try:
            with socket.create_connection((settings.REDIS_HOST, settings.REDIS_PORT), timeout=0.1):
                cls._redis_online = True
                cls._redis_check_time = now
                return True
        except OSError:
            cls._redis_online = False
            cls._redis_check_time = now
            return False

    @classmethod
    async def publish_event(
        cls,
        job_id: str,
        stage: str,
        progress: float,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        if not cls._is_redis_online():
            return

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
