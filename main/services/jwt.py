import jwt
from datetime import timedelta, datetime
from main.config import settings

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class JwtAuth:
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXP_MINUTES = 30
    SECRET_KEY = settings.SECRET_KEY

    async def create_access_token(self, user_id: str) -> str:
        data_to_encode = {"sub": user_id}
        exp_time = datetime.now() + timedelta(minutes=self.ACCESS_TOKEN_EXP_MINUTES)
        data_to_encode.update({"exp": exp_time})
        encoded_jwt = jwt.encode(
            data_to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM
        )
        return encoded_jwt

    async def decode_token(self, token: str) -> str:
        try:
            data = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise Exception("Token expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
        return data.get("sub")


"""def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = JwtAuth.decode_token(token)
        user_id = payload.get("sub")
        exp_time = payload.get("exp")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="не могу валидировать токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if exp_time > datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен невалидный",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )"""
