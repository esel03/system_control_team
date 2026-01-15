from pydantic import BaseModel, EmailStr


class RegistrationIn(BaseModel):
    email: EmailStr
    first_name: str
    patronymic_name: str | None = None
    last_name: str
    password: str


class RegistrationOut(BaseModel):
    email: str


class GetToken(BaseModel):
    refresh_token: str

class OutToken(BaseModel):
    refresh_token: str