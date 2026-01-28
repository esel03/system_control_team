from fastapi import APIRouter, Depends
from main.db.connect import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from main.api.auth import get_auth_service
from main.services.auth import AuthRegUserServices
from main.services.auth import oauth2_scheme
from main.services.team_management import RoomTeamServices
from main.repositories.team_management import RoomTeamRepository
from main.schemas.team_management import (
    RoomOut,
    AddToRoomIn,
    CreateRoomOut,
    ListRoom,
    ListUserOut,
)
from uuid import UUID
import random
from datetime import datetime

router = APIRouter(prefix="/room", tags=["room"])


def get_team_service(
    session: AsyncSession = Depends(get_async_session),
) -> RoomTeamServices:
    repo = RoomTeamRepository(db=session)
    return RoomTeamServices(repository=repo)


@router.get(
    "/create_room/{name}", summary="Создание комнаты", response_model=CreateRoomOut
)
async def create_room_name(
    name: str,
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> CreateRoomOut:
    result = await service_auth.get_current_user(token=token)
    return await service.create_room(user_id=result.user_id, name=name)


@router.get("/create_room/", summary="Создание комнаты", response_model=CreateRoomOut)
async def create_room(
    name: str = f'КОМНАТА:{(datetime.now().date()).strftime("%Y-%m-%d")}-{random.randint(1000000, 9999999)}',
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> CreateRoomOut:
    result = await service_auth.get_current_user(token=token)
    return await service.create_room(user_id=result.user_id, name=name)


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
    result = await service_auth.get_current_user(token=token)
    await service.access_right_user_in_room(
        user_id=result.user_id, room_id=data.room_id
    )
    return RoomOut(
        room_id=await service.add_people_to_room(
            room_id=data.room_id, data=data.list_users
        )
    )


@router.get(
    "/get_list_rooms",
    summary="Получение всех комнат пользователя",
    response_model=ListRoom,
)
async def get_list_rooms(
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> ListRoom:
    result = await service_auth.get_current_user(token=token)
    return await service.get_list_rooms(user_id=result.user_id)


@router.get(
    "/get_list_users_rooms/{room_id}",
    summary="Получение всех юзеров в комнате",
    response_model=ListUserOut,
)
async def get_list_users_rooms(
    room_id: str,
    token: str = Depends(oauth2_scheme),
    service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> ListUserOut:
    await service_auth.get_current_user(token=token)
    return await service.get_list_users_rooms(room_id=UUID(room_id))
