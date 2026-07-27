import redis.asyncio as redis

from main.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    encoding="utf-8",
    socket_connect_timeout=3,
    socket_timeout=3,
    health_check_interval=30,
)
