from uuid import UUID
from pydantic import BaseModel, EmailStr


class RegistrationIn(BaseModel):
    email: EmailStr
    first_name: str
    patronymic_name: str | None = None
    last_name: str
    password: str


class RegistrationOut(BaseModel):
<<<<<<< HEAD
    email: str


class GetToken(BaseModel):
    refresh_token: str

class OutToken(BaseModel):
    refresh_token: str
=======
    email: EmailStr


class LogIn(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: UUID
>>>>>>> main
