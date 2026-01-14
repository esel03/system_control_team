"""
Процедура регистрации и осуществления подтверждения почты
"""

from uuid import UUID
from main.repositories.auth import AuthRegUserRepository
from main.services.jwt import JwtAuth

from fastapi import HTTPException
from main.schemas.auth import RegistrationIn
from dataclasses import dataclass
from pwdlib import PasswordHash

jwt_token = JwtAuth()


@dataclass
class AuthRegUserServices:
    repository: AuthRegUserRepository
    password_hash = PasswordHash.recommended()

    async def registration_services(self, data: RegistrationIn) -> str:
        if await self.check_email(email=data.email):
            raise HTTPException(status_code=404, detail="Email занят")
        data.password = await self.get_password_hash(password=data.password)
        return await jwt_token.create_access_token(
            user_id=str(await self.write_user(data=data))
        )

    async def get_password_hash(self, password) -> str:
        return self.password_hash.hash(password)

    async def verify_password(self, plain_password, hashed_password) -> bool:
        return self.password_hash.verify(plain_password, hashed_password)

    async def check_email(self, email) -> str | None:
        return await self.repository.get_email(email=email)

    async def write_user(self, data) -> UUID:
        return await self.repository.create_user(data=data)
