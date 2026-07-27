from fastapi import HTTPException, status
from redis.exceptions import RedisError

from main.redis import redis_client


async def enforce_rate_limit(
    identity: str,
    action: str,
    limit: int,
    window_seconds: int,
) -> None:
    key = f"rate:{action}:{identity}"
    try:
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, window_seconds)
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис авторизации временно недоступен",
        ) from exc

    if current > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много запросов, повторите позже",
            headers={"Retry-After": str(window_seconds)},
        )
