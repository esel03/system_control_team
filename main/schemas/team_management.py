from uuid import UUID
from pydantic import BaseModel


class UsersList(BaseModel):
    user_id: UUID
    role: str | None = "неопределена"
    tag: str | None = "неопределена"
    is_chief: bool = False


class CreateRoomIn(BaseModel):
    name: str
    list_users: list[UUID]


class CreateTeamIn(BaseModel):
    name: str
    room_id: UUID
    list_users: list[UsersList]


class DeleteTeamPeople(BaseModel):
    team_id: UUID
    list_users: list[UUID]


class DeleteRoomPeople(BaseModel):
    room_id: UUID
    list_users: list[UUID]


class AddToTeamIn(BaseModel):
    name: str
    team_id: UUID
    list_users: list[UsersList]


class AddToTeamOut(BaseModel):
    team_id: UUID
    list_users: list[UUID]


class NumUsId(BaseModel):
    existing_user_id: set
    in_data: set


class RoomOut(BaseModel):
    room_id: UUID


class ListRoom(BaseModel):
    list_rooms: list


class ListUserOut(BaseModel):
    list_users: list


class ListTeam(BaseModel):
    list_teams: list


class UserListRoom(BaseModel):
    user_id: UUID
    is_chief: bool = False


class CreateRoomOut(BaseModel):
    room_id: UUID


class AddToRoomIn(BaseModel):
    room_id: UUID
    list_users: list[UserListRoom]


class TeamOut(BaseModel):
    team_id: UUID
