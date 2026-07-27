import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from main.api import auth, health, room, tasks, team_management
from main.config import settings
from main.db.connect import engine
from main.logging import configure_logging
from main.middleware import RequestContextMiddleware
from main.redis import redis_client

configure_logging(settings.ENVIRONMENT)
logger = logging.getLogger(__name__)

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        send_default_pii=False,
        traces_sample_rate=0.1,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("application_started environment=%s", settings.ENVIRONMENT)
    yield
    await redis_client.aclose()
    await engine.dispose()
    logger.info("application_stopped")


app = FastAPI(
    title="System Control Team API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    RequestContextMiddleware,
    max_body_bytes=settings.MAX_REQUEST_BODY_BYTES,
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts or ["*"],
)
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials="*" not in settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    logger.exception(
        "database_error path=%s request_id=%s",
        request.url.path,
        getattr(request.state, "request_id", None),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка хранилища данных"},
    )


app.include_router(auth.router, prefix="/api/v1")
app.include_router(room.router, prefix="/api/v1")
app.include_router(team_management.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(health.router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "service": "System Control Team API",
        "version": app.version,
        "docs": "/docs",
        "health": "/health/ready",
    }
