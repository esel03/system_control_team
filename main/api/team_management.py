from fastapi import APIRouter, Depends
from main.db.connect import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from main.api.auth import get_auth_service
from main.services.auth import AuthRegUserServices
from main.services.auth import oauth2_scheme
from main.services.team_management import RoomTeamServices
from main.repositories.team_management import RoomTeamRepository
from main.schemas.team_management import (
    CreateRoomIn,
    RoomOut,
    AddToRoomIn,
    CreateTeamIn,
    TeamOut,
    AddToTeamIn,
    DeleteTeamPeople,
    DeleteRoomPeople,
)
from main.services.auth import oauth2_scheme


router = APIRouter(prefix="/team", tags=["team"])


def get_team_service(
    session: AsyncSession = Depends(get_async_session),
) -> RoomTeamServices:
    repo = RoomTeamRepository(db=session)
    return RoomTeamServices(repository=repo)


@router.post("/create_room", summary="Создание комнаты", response_model=RoomOut)
async def create_room(
    data: CreateRoomIn,
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> RoomOut:
    await service_auth.get_current_user(token=token)
    return RoomOut(room_id=await service.create_room(data=data))


@router.post(
    "/add_people_to_room",
    summary="Добавление участника/ов в комнату",
    response_model=RoomOut,
)
async def add_people_to_room(
    data: AddToRoomIn,
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> RoomOut:
    await service_auth.get_current_user(token=token)
    return RoomOut(
        room_id=await service.add_people_to_room(room_id=data.room_id, data=data)
    )


@router.post(
    "/delete_people_to_room",
    summary="Удаление участника/ов из комнаты",
    response_model=RoomOut,
)
async def delete_people_to_room(
    data: DeleteRoomPeople,
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> RoomOut:
    await service_auth.get_current_user(token=token)
    return RoomOut(
        room_id=await service.delete_people_to_room(room_id=data.room_id, data=data)
    )


# TODO: юзер создающий команду должен быть в data: CreateTeamIn,
# с определением role и tag, и статусом is_сhief
@router.post("/create_team", summary="Создание команды", response_model=TeamOut)
async def create_team(
    data: CreateTeamIn,
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> TeamOut:
    await service_auth.get_current_user(token=token)
    return TeamOut(team_id=await service.create_team(data=data))


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
    await service_auth.get_current_user(token=token)
    return TeamOut(team_id=await service.add_people_to_team(data=data))



@router.post(
    "/delete_people_to_team",
    summary="Удаление участника/ов из команды",
    response_model=TeamOut,
)
async def delete_people_to_team(
    data: DeleteTeamPeople, token: str = Depends(oauth2_scheme), service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> TeamOut:
    await service_auth.get_current_user(token=token)
    return TeamOut(team_id=await service.delete_people_to_team(data=data))



@router.get("/get_rooms", summary="Получение всех комнат пользователя", response_model=RoomOut)
async def get_rooms(
    token: str = Depends(oauth2_scheme), service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> RoomOut:
    result = await service_auth.get_current_user(token=token)
    return await service.get_list_rooms(user_id=result.user_id)

# TODO: завтра доделать, список пользователей в комнате
@router.get("/get_users_in_rooms", summary="Получение всех комнат пользователя", response_model=RoomOut)
async def get_rooms(
    token: str = Depends(oauth2_scheme), service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> RoomOut:
    result = await service_auth.get_current_user(token=token)
    return await service.get_list_rooms(user_id=result.user_id)
    
