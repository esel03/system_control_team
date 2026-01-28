from fastapi import APIRouter, Depends
from main.db.connect import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from main.api.auth import get_auth_service
from main.services.auth import AuthRegUserServices
from main.services.auth import oauth2_scheme
from main.services.team_management import RoomTeamServices
from main.repositories.team_management import RoomTeamRepository
from main.schemas.team_management import (
    TeamOut,
    AddToTeamIn,
    ListTeam,
    ListUserOut,
)
from uuid import UUID
import random
from datetime import datetime


router = APIRouter(prefix="/team", tags=["team"])


def get_team_service(
    session: AsyncSession = Depends(get_async_session),
) -> RoomTeamServices:
    repo = RoomTeamRepository(db=session)
    return RoomTeamServices(repository=repo)


@router.get(
    "/create_team/{room_id}/{name}", summary="Создание команды", response_model=TeamOut
)
async def create_team_name(
    room_id: str,
    name: str,
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> TeamOut:
    result = await service_auth.get_current_user(token=token)
    return TeamOut(
        team_id=await service.create_team(
            user_id=result.user_id, room_id=room_id, name=name
        )
    )


@router.get(
    "/create_team/{room_id}", summary="Создание команды", response_model=TeamOut
)
async def create_team(
    room_id: str,
    name: str = f'Команда:{(datetime.now().date()).strftime("%Y-%m-%d")}-{random.randint(10000, 99999)}',
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> TeamOut:
    result = await service_auth.get_current_user(token=token)
    return TeamOut(
        team_id=await service.create_team(
            user_id=result.user_id, room_id=room_id, name=name
        )
    )


@router.post(
    "/add_people_to_team",
    summary="Добавление участника/ов в команду",
    response_model=TeamOut,
)
async def add_people_to_team(
    data: AddToTeamIn,
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> TeamOut:
    result = await service_auth.get_current_user(token=token)
    await service.access_right_user_in_team(
        user_id=result.user_id, team_id=data.team_id
    )
    return await service.add_people_to_team(user_id=result.user_id, data=data)


@router.get(
    "/get_list_teams/{room_id}",
    summary="Получение всех команд пользователя",
    response_model=ListTeam,
)
async def get_rooms(
    room_id: str,
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> ListTeam:
    result = await service_auth.get_current_user(token=token)
    return await service.get_list_teams(user_id=result.user_id, room_id=UUID(room_id))


@router.get(
    "/get_list_users_teams/{team_id}",
    summary="Получение всех юзеров в комнате",
    response_model=ListUserOut,
)
async def get_list_users_teams(
    team_id: str,
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> ListUserOut:
    await service_auth.get_current_user(token=token)
    return await service.get_list_users_teams(team_id=UUID(team_id))
