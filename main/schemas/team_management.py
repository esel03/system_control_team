from uuid import UUID
from pydantic import BaseModel


class UsersList(BaseModel):
    user_id: UUID
    role: str | None = None
    tag: str | None = None
    is_chief: bool = False


class CreateRoomIn(BaseModel):
    name: str
    list_role: list[str]
    list_tag: list[str]
    list_users: list[UsersList]


class CreateTeamIn(BaseModel):
    name: str
    room_id: UUID
    list_users: list[UsersList]


class RoomOut(BaseModel):
    room_id: UUID


class AddToRoomIn(BaseModel):
    room_id: UUID
    list_users: list[UsersList]
