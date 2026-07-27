from datetime import date
from secrets import token_hex
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def default_room_name() -> str:
    return f"Комната-{date.today().isoformat()}-{token_hex(3)}"


def default_team_name() -> str:
    return f"Команда-{date.today().isoformat()}-{token_hex(3)}"


class RoomCreate(BaseModel):
    name: str = Field(default_factory=default_room_name, min_length=1, max_length=50)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()


class TeamCreate(BaseModel):
    name: str = Field(default_factory=default_team_name, min_length=1, max_length=50)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()


class RoomMemberIn(BaseModel):
    user_id: UUID
    is_chief: bool = False


class TeamMemberIn(BaseModel):
    user_id: UUID
    role: str = Field(default="неопределена", min_length=1, max_length=100)
    tag: str = Field(default="неопределена", min_length=1, max_length=100)
    is_chief: bool = False

    @field_validator("role", "tag", mode="before")
    @classmethod
    def strip_member_data(cls, value: str) -> str:
        return value.strip()


class AddRoomMembersIn(BaseModel):
    members: list[RoomMemberIn] = Field(min_length=1, max_length=100)


class AddTeamMembersIn(BaseModel):
    members: list[TeamMemberIn] = Field(min_length=1, max_length=100)


class RemoveMembersIn(BaseModel):
    user_ids: list[UUID] = Field(min_length=1, max_length=100)


class RoomOut(BaseModel):
    room_id: UUID


class TeamOut(BaseModel):
    team_id: UUID


class RoomSummary(BaseModel):
    room_id: UUID
    name: str


class TeamSummary(BaseModel):
    team_id: UUID
    name: str


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: EmailStr
    last_name: str
    first_name: str
    patronymic_name: str | None = None
    is_chief: bool
    role: str | None = None
    tag: str | None = None


class RoomListOut(BaseModel):
    items: list[RoomSummary]


class TeamListOut(BaseModel):
    items: list[TeamSummary]


class UserListOut(BaseModel):
    items: list[UserSummary]
