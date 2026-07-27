from fastapi import APIRouter, Depends, HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from main.db.connect import get_async_session
from main.redis import redis_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", include_in_schema=False)
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", include_in_schema=False)
async def readiness(
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
        await redis_client.ping()
    except (SQLAlchemyError, RedisError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис не готов принимать запросы",
        ) from exc
    return {"status": "ready"}
