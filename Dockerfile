FROM python:3.13-slim AS dependencies

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY requirements.txt .
RUN python -m pip install --prefix=/install -r requirements.txt


FROM python:3.13-slim AS runtime

ARG APP_UID=10001
ARG APP_GID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PORT=8000 \
    WEB_CONCURRENCY=1 \
    FORWARDED_ALLOW_IPS=127.0.0.1

LABEL org.opencontainers.image.title="System Control Team API" \
      org.opencontainers.image.description="FastAPI backend for rooms, teams and tasks"

RUN groupadd --gid "${APP_GID}" app \
    && useradd \
        --uid "${APP_UID}" \
        --gid "${APP_GID}" \
        --create-home \
        --shell /usr/sbin/nologin \
        app

COPY --from=dependencies /install /usr/local

WORKDIR /app

COPY --chown=app:app alembic ./alembic
COPY --chown=app:app main ./main
COPY --chown=app:app alembic.ini requirements.txt start.sh migrate.sh ./

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=3)"]

STOPSIGNAL SIGTERM

CMD ["./start.sh"]
