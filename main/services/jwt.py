from fastapi import HTTPException
import jwt
from fastapi import status
from dataclasses import dataclass
from datetime import timedelta, datetime
from main.config import settings
from main.redis import redis_client

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@dataclass
class JwtAuth:
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXP_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 1
    SECRET_KEY = settings.SECRET_KEY

    async def create_access_token(self, user_id: str) -> dict[str, str]:
        access_token = await self._create_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=self.ACCESS_TOKEN_EXP_MINUTES),
        )

        refresh_token = await self._create_token(
            data={"sub": user_id},
            expires_delta=timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS),  # days
        )

        await redis_client.setex(
            name=refresh_token,
            time=timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS),
            value=user_id,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def _create_token(self, data: dict, expires_delta: timedelta) -> str:
        expire = datetime.now() + expires_delta
        data.update({"exp": expire})
        return jwt.encode(data, self.SECRET_KEY, algorithm=self.ALGORITHM)

    async def decode_token(self, token: str) -> dict:
        try:
            data = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
        return data.get("sub")

    async def new_access_token(self, refresh_token: str) -> str:
        user_id = await redis_client.get(refresh_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await self._create_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=self.ACCESS_TOKEN_EXP_MINUTES),
        )

    async def delete_refresh_token(self, refresh_token: str) -> dict[str, str]:
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Требуется refresh_token",
            )

        deleted = await redis_client.delete(refresh_token)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный или уже отозванный refresh token",
            )
        return {"detail": "Вы успешно вышли из аккаунта"}
