"""
Процедура регистрации и осуществления подтверждения почты
"""

from main.repositories.auth import AuthRegUserRepository

from fastapi import HTTPException
from main.schemas.auth import RegistrationIn
from dataclasses import dataclass
from pwdlib import PasswordHash


@dataclass
class AuthRegUserServices:
    repository: AuthRegUserRepository
    password_hash = PasswordHash.recommended()

    async def registration_services(self, data: RegistrationIn):
        if await self.check_email(email=data.email):
            raise HTTPException(status_code=404, detail="Email занят")
        data.password = await self.get_password_hash(password=data.password)
        return {"token": f"{(await self.write_user(data=data))}"}

    async def get_password_hash(self, password):
        return self.password_hash.hash(password)

    async def verify_password(self, plain_password, hashed_password):
        return self.password_hash.verify(plain_password, hashed_password)

    async def check_email(self, email):
        return await self.repository.get_email(email=email)

    async def write_user(self, data):
        return await self.repository.create_user(data=data)
