"""
Процедура регистрации и осуществления подтверждения почты
"""

from uuid import UUID
from main.repositories.auth import AuthRegUserRepository
from main.services.jwt import JwtAuth
from main.services.utils import Utils

from fastapi import HTTPException, status
from main.schemas.auth import RegistrationIn
from dataclasses import dataclass

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
    
    async def update_token(self, data) -> str:
        return await self.jwt_token.new_access_token(data=data)

