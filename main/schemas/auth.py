import uuid
from pydantic import BaseModel, EmailStr


class RegistrationIn(BaseModel):
    email: EmailStr
    first_name: str
    patronymic_name: str | None = None
    last_name: str
    password: str


class RegistrationOut(BaseModel):
    email: EmailStr


class GetToken(BaseModel):
    refresh_token: str


class OutToken(BaseModel):
    access_token: str


class LogIn(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: uuid.UUID


class LogoutRequest(BaseModel):
    refresh_token: str
