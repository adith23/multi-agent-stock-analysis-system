from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator
from uuid import uuid4

from django.conf import settings
import redis
import redis.asyncio as aioredis

from .sse import SSEJSONEncoder

logger = logging.getLogger(__name__)


def _get_redis_url() -> str:
    return getattr(settings, "REDIS_URL", "redis://localhost:6379/0")


class EventBus:
    """Redis-backed real-time event bus for SSE pub/sub."""

    @staticmethod
    def _serialize(event_type: str, data: Any, event_id: str | None = None) -> str:
        return json.dumps(
            {
                "id": event_id or str(uuid4()),
                "event": event_type,
                "data": data,
            },
            cls=SSEJSONEncoder,
        )

    @classmethod
    def publish_pipeline_event(
        cls,
        run_id: str,
        event_type: str,
        data: Any,
        event_id: str | None = None,
    ) -> None:
        """Publish a pipeline stage progress/completion event to Redis channel."""
        channel = f"pipeline:{run_id}"
        message = cls._serialize(event_type, data, event_id=event_id)
        try:
            client = redis.from_url(_get_redis_url(), decode_responses=True)
            client.publish(channel, message)
        except Exception as exc:
            logger.warning(
                "Failed to publish event %s to channel %s: %s",
                event_type,
                channel,
                exc,
            )

    @classmethod
    def publish_alert_event(
        cls,
        event_type: str,
        data: Any,
        event_id: str | None = None,
    ) -> None:
        """Publish a global alert event (regime transition, exit trigger) to alerts:stream channel."""
        channel = "alerts:stream"
        message = cls._serialize(event_type, data, event_id=event_id)
        try:
            client = redis.from_url(_get_redis_url(), decode_responses=True)
            client.publish(channel, message)
        except Exception as exc:
            logger.warning(
                "Failed to publish alert %s to channel %s: %s",
                event_type,
                channel,
                exc,
            )

    @classmethod
    async def listen_channel(
        cls,
        channel: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Asynchronously listen to a Redis pub/sub channel yielding parsed event dicts."""
        client = None
        pubsub = None
        try:
            client = aioredis.from_url(_get_redis_url(), decode_responses=True)
            pubsub = client.pubsub()
            await pubsub.subscribe(channel)

            async for message in pubsub.listen():
                if message.get("type") == "message":
                    raw_data = message.get("data")
                    if raw_data:
                        try:
                            parsed = json.loads(raw_data)
                            yield parsed
                        except Exception as exc:
                            logger.error("Error decoding pubsub message on %s: %s", channel, exc)
        except Exception as exc:
            logger.warning("Redis pubsub listener exception on channel %s: %s", channel, exc)
            raise
        finally:
            if pubsub:
                try:
                    await pubsub.unsubscribe(channel)
                    await pubsub.close()
                except Exception:
                    pass
            if client:
                try:
                    await client.close()
                except Exception:
                    pass
