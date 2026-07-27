from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from main.api.auth import get_current_user
from main.db.connect import get_async_session
from main.repositories.team_management import RoomTeamRepository
from main.schemas.auth import TokenData
from main.schemas.team_management import (
    AddRoomMembersIn,
    RemoveMembersIn,
    RoomCreate,
    RoomListOut,
    RoomOut,
    UserListOut,
)
from main.services.team_management import RoomTeamServices

router = APIRouter(prefix="/rooms", tags=["rooms"])


def get_room_team_service(
    session: AsyncSession = Depends(get_async_session),
) -> RoomTeamServices:
    return RoomTeamServices(repository=RoomTeamRepository(db=session))


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
async def create_room(
    data: RoomCreate,
    current_user: TokenData = Depends(get_current_user),
    service: RoomTeamServices = Depends(get_room_team_service),
) -> RoomOut:
    room_id = await service.create_room(current_user.user_id, data.name)
    return RoomOut(room_id=room_id)


@router.get("", response_model=RoomListOut)
async def get_rooms(
    current_user: TokenData = Depends(get_current_user),
    service: RoomTeamServices = Depends(get_room_team_service),
) -> RoomListOut:
    return RoomListOut(items=await service.get_rooms(current_user.user_id))


@router.get("/{room_id}/members", response_model=UserListOut)
async def get_room_members(
    room_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    service: RoomTeamServices = Depends(get_room_team_service),
) -> UserListOut:
    members = await service.get_room_members(current_user.user_id, room_id)
    return UserListOut(items=members)


@router.post("/{room_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def add_room_members(
    room_id: UUID,
    data: AddRoomMembersIn,
    current_user: TokenData = Depends(get_current_user),
    service: RoomTeamServices = Depends(get_room_team_service),
) -> Response:
    await service.add_room_members(current_user.user_id, room_id, data.members)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{room_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def remove_room_members(
    room_id: UUID,
    data: RemoveMembersIn,
    current_user: TokenData = Depends(get_current_user),
    service: RoomTeamServices = Depends(get_room_team_service),
) -> Response:
    await service.remove_room_members(current_user.user_id, room_id, data.user_ids)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
