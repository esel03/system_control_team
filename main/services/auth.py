"""
Процедура регистрации и осуществления подтверждения почты
"""
from fastapi import FastAPI, HTTPException
from main.schemas.auth import RegistrationIn
from dataclasses import dataclass
from pwdlib import PasswordHash

@dataclass
class AuthRegUsersServices:
    password_hash = PasswordHash.recommended()

    async def registration_services(self, data):
        if not (await self.check_email(email=data.email)):
            raise HTTPException(status_code=404, detail="Email is buzy")
        await self.get_password_hash(password=data.password)

        


    async def get_password_hash(self, password):
        return self.password_hash.hash(password)
    
    async def verify_password(self, plain_password, hashed_password):
        return self.password_hash.verify(plain_password, hashed_password)
    
    async def check_email(self, email):

    
    async def write_user(self, )
        

