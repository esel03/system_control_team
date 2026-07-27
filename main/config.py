from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: SecretStr
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    SECRET_KEY: SecretStr = Field(min_length=32)
    REDIS_URL: str

    ENVIRONMENT: str = "development"
    SQL_ECHO: bool = False
    SENTRY_DSN: str | None = None
    ALLOWED_HOSTS: str = "*"
    CORS_ORIGINS: str = ""
    MAX_REQUEST_BODY_BYTES: int = 1_048_576
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=5, le=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=1, ge=1, le=30)

    model_config = SettingsConfigDict(
        env_file=Path(__file__).with_name(".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_db_url(self) -> str:
        return self._database_url("postgresql+asyncpg")

    def get_sync_db_url(self) -> str:
        return self._database_url("postgresql+psycopg")

    def _database_url(self, drivername: str) -> str:
        unix_socket = self.DB_HOST.startswith("/")
        return URL.create(
            drivername=drivername,
            username=self.DB_USER,
            password=self.DB_PASSWORD.get_secret_value(),
            host=None if unix_socket else self.DB_HOST,
            port=None if unix_socket else self.DB_PORT,
            database=self.DB_NAME,
            query=(
                {"host": self.DB_HOST, "port": str(self.DB_PORT)} if unix_socket else {}
            ),
        ).render_as_string(hide_password=False)

    @property
    def allowed_hosts(self) -> list[str]:
        return [item.strip() for item in self.ALLOWED_HOSTS.split(",") if item.strip()]

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]


settings = Settings()
