from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from fastapi import HTTPException, status

from main.config import settings
from main.redis import redis_client


@dataclass
class JwtAuth:
    ALGORITHM = "HS256"
    ISSUER = "system-control-team"
    AUDIENCE = "system-control-team-api"
    SECRET_KEY = settings.SECRET_KEY.get_secret_value()

    @property
    def access_lifetime(self) -> timedelta:
        return timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    @property
    def refresh_lifetime(self) -> timedelta:
        return timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    async def create_token_pair(self, user_id: str) -> dict[str, str]:
        access_token = self._create_token(
            user_id=user_id,
            token_type="access",
            lifetime=self.access_lifetime,
        )
        refresh_token = self._create_token(
            user_id=user_id,
            token_type="refresh",
            lifetime=self.refresh_lifetime,
        )
        refresh_payload = self.decode_token(refresh_token, expected_type="refresh")
        await redis_client.setex(
            self._refresh_key(refresh_payload["jti"]),
            self.refresh_lifetime,
            user_id,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def _create_token(
        self,
        user_id: str,
        token_type: str,
        lifetime: timedelta,
    ) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": user_id,
            "typ": token_type,
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + lifetime,
            "iss": self.ISSUER,
            "aud": self.AUDIENCE,
        }
        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def decode_token(self, token: str, expected_type: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self.SECRET_KEY,
                algorithms=[self.ALGORITHM],
                audience=self.AUDIENCE,
                issuer=self.ISSUER,
                options={"require": ["sub", "typ", "jti", "iat", "exp"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise self._unauthorized("Срок действия токена истёк") from exc
        except jwt.InvalidTokenError as exc:
            raise self._unauthorized("Некорректный токен") from exc

        if payload.get("typ") != expected_type:
            raise self._unauthorized("Некорректный тип токена")
        return payload

    async def rotate_refresh_token(self, refresh_token: str) -> dict[str, str]:
        payload = self.decode_token(refresh_token, expected_type="refresh")
        key = self._refresh_key(payload["jti"])
        stored_user_id = await redis_client.getdel(key)
        if not stored_user_id or stored_user_id != payload["sub"]:
            raise self._unauthorized("Refresh token отозван или уже использован")
        return await self.create_token_pair(stored_user_id)

    async def revoke_refresh_token(
        self,
        refresh_token: str,
        expected_user_id: str,
    ) -> None:
        payload = self.decode_token(refresh_token, expected_type="refresh")
        if payload["sub"] != expected_user_id:
            raise self._unauthorized("Токен принадлежит другому пользователю")
        deleted = await redis_client.delete(self._refresh_key(payload["jti"]))
        if not deleted:
            raise self._unauthorized("Refresh token уже отозван")

    @staticmethod
    def _refresh_key(jti: str) -> str:
        return f"auth:refresh:{jti}"

    @staticmethod
    def _unauthorized(detail: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
