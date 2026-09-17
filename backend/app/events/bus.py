import redis.asyncio as redis

from app.config import settings
from app.events.schemas import EventoEnvelope

CANAL_EVENTOS = "eventos:all"

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def publish_event(evento: EventoEnvelope) -> None:
    client = get_redis()
    await client.publish(CANAL_EVENTOS, evento.model_dump_json())
