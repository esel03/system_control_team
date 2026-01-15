from fastapi import HTTPException
import jwt
from dataclasses import dataclass
from datetime import timedelta, datetime
from main.config import settings
from uuid import UUID


@dataclass
class JwtAuth:
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXP_MINUTES = 30
    SECRET_KEY = settings.SECRET_KEY

    async def create_access_token(self, user_id: UUID) -> str:
        data_to_encode = {"sub": str(user_id)}
        exp_time = datetime.now() + timedelta(minutes=self.ACCESS_TOKEN_EXP_MINUTES)
        data_to_encode.update({"exp": exp_time})
        encoded_jwt = jwt.encode(
            data_to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_jwt

    async def decode_token(self, token: str) -> dict:
        try:
            data = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        return data
