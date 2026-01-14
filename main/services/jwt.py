import jwt
from datetime import timedelta, datetime
from main.config import Token

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class JwtAuth:
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXP_MINUTES = 15
    SECRET_KEY = Token().SECRET_KEY

    @staticmethod
    def create_access_token(user_id: str) -> str:
        data_to_encode = {"sub": user_id}
        exp_time = datetime.now() + timedelta(minutes=JwtAuth.ACCESS_TOKEN_EXP_MINUTES)
        data_to_encode.update({"exp": exp_time})
        encoded_jwt = jwt.encode(
            data_to_encode, JwtAuth.SECRET_KEY, algorithm=JwtAuth.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> str:
        try:
            data = jwt.decode(token, JwtAuth.SECRET_KEY, algorithms=[JwtAuth.ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise Exception("Token expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
        return data.get("sub")


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = JwtAuth.decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="не могу валидировать токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
