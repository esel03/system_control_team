# main/redis.py
import redis.asyncio as redis
from main.config import settings

# Асинхронный Redis клиент
redis_client = redis.from_url(
    settings.REDIS_URL,  
    decode_responses=True,  
    encoding="utf-8"
)
