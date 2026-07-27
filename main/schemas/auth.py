import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegistrationIn(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    patronymic_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator(
        "first_name",
        "last_name",
        "patronymic_name",
        mode="before",
    )
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class RegistrationOut(BaseModel):
    email: EmailStr


class GetToken(BaseModel):
    refresh_token: str = Field(min_length=20)


class OutToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class Token(OutToken):
    pass


class TokenData(BaseModel):
    user_id: uuid.UUID


class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    patronymic_name: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class MessageOut(BaseModel):
    detail: str


class ErrorOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detail: str
