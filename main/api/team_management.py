from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from main.api.auth import get_current_user
from main.db.connect import get_async_session
from main.repositories.team_management import RoomTeamRepository
from main.schemas.auth import TokenData
from main.schemas.team_management import (
    AddTeamMembersIn,
    RemoveMembersIn,
    TeamCreate,
    TeamListOut,
    TeamOut,
    UserListOut,
)
from main.services.team_management import RoomTeamServices

router = APIRouter(tags=["teams"])


def get_room_team_service(
    session: AsyncSession = Depends(get_async_session),
) -> RoomTeamServices:
    return RoomTeamServices(repository=RoomTeamRepository(db=session))


@router.post(
    "/rooms/{room_id}/teams",
    response_model=TeamOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_team(
    room_id: UUID,
    data: TeamCreate,
    current_user: TokenData = Depends(get_current_user),
    service: RoomTeamServices = Depends(get_room_team_service),
) -> TeamOut:
    team_id = await service.create_team(current_user.user_id, room_id, data.name)
    return TeamOut(team_id=team_id)


@router.get("/rooms/{room_id}/teams", response_model=TeamListOut)
async def get_teams(
    room_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    service: RoomTeamServices = Depends(get_room_team_service),
) -> TeamListOut:
    teams = await service.get_teams(current_user.user_id, room_id)
    return TeamListOut(items=teams)


@router.get("/teams/{team_id}/members", response_model=UserListOut)
async def get_team_members(
    team_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    service: RoomTeamServices = Depends(get_room_team_service),
) -> UserListOut:
    members = await service.get_team_members(current_user.user_id, team_id)
    return UserListOut(items=members)


@router.post("/teams/{team_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def add_team_members(
    team_id: UUID,
    data: AddTeamMembersIn,
    current_user: TokenData = Depends(get_current_user),
    service: RoomTeamServices = Depends(get_room_team_service),
) -> Response:
    await service.add_team_members(current_user.user_id, team_id, data.members)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/teams/{team_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_members(
    team_id: UUID,
    data: RemoveMembersIn,
    current_user: TokenData = Depends(get_current_user),
    service: RoomTeamServices = Depends(get_room_team_service),
) -> Response:
    await service.remove_team_members(current_user.user_id, team_id, data.user_ids)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
