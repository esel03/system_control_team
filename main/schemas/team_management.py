from uuid import UUID
from pydantic import BaseModel, EmailStr


class UsersList(BaseModel):
    user_id: UUID
    role: str
    tag: str

class CreateRoomIn(BaseModel):
    name: str
    list_role: list[str]
    list_tag: list[str]
    list_users: list[UsersList]


class RoomOut(BaseModel):
    room_id: UUID