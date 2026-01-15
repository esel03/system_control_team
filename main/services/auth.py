"""
Процедура регистрации и осуществления подтверждения почты
"""

from typing import Annotated
from uuid import UUID
from main.repositories.auth import AuthRegUserRepository
from main.services.jwt import JwtAuth
from main.services.utils import Utils

<<<<<<< HEAD
from fastapi import HTTPException, status
from main.schemas.auth import RegistrationIn
=======
from fastapi import Depends, HTTPException, status
from main.schemas.auth import RegistrationIn, LogIn, Token, TokenData
>>>>>>> main
from dataclasses import dataclass
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
jwt_token = JwtAuth()
utils = Utils()


@dataclass
class AuthRegUserServices:
    repository: AuthRegUserRepository

    async def registration_services(self, data: RegistrationIn) -> str:
        if await self._check_email(email=data.email):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Email занят")
        data.password = await utils.get_password_hash(password=data.password)
        return await self._write_user(data=data)

    async def _check_email(self, email) -> str | None:
        return await self.repository.get_email(email=email)

    async def _write_user(self, data) -> str:
        return await self.repository.create_user(data=data)
<<<<<<< HEAD
    
    async def update_token(self, data) -> str:
        return await self.jwt_token.new_access_token(data=data)

=======

    async def _login_service(self, data: LogIn) -> Token:
        user = await self.repository.get_user(data=data)
        if not user:
            raise HTTPException(status_code=401, detail="пользователь не существует")
        if not await utils.verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="неверные данные для входа")
        token = await jwt_token.create_access_token(user.user_id)
        return Token(access_token=token, token_type="bearer")

    async def _get_current_user(
        self, token: Annotated[str, Depends(oauth2_scheme)]
    ) -> TokenData:
        try:
            payload = await jwt_token.decode_token(token)
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="не могу валидировать токен",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return TokenData(user_id=UUID(user_id))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
>>>>>>> main
