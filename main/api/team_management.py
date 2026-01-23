from typing import Annotated
from fastapi import APIRouter, Depends
from main.db.connect import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from main.api.auth import get_auth_service
from main.services.auth import AuthRegUserServices
from main.services.team_management import RoomTeamServices
from main.repositories.team_management import RoomTeamRepository
from main.schemas.team_management import (
    CreateRoomIn,
    RoomOut,
    AddToRoomIn,
    CreateTeamIn
)

router = APIRouter(prefix="/team", tags=["team"])


def get_team_service(
    session: AsyncSession = Depends(get_async_session),
) -> RoomTeamServices:
    repo = RoomTeamRepository(db=session)
    return RoomTeamServices(repository=repo)



@router.post("/create_room", summary="Создание комнаты", response_model=RoomOut)
async def create_room(token: str,
    data: CreateRoomIn, service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> RoomOut:
    result = await service_auth.get_current_user(token=token)
    return RoomOut(room_id=await service.create_room(user_id=result.user_id, data=data))



@router.post("/add_people_to_room", summary="Добавление участника/ов в комнату", response_model=RoomOut)
async def add_people_to_room(token: str,
    data: AddToRoomIn, service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> RoomOut:
    await service_auth.get_current_user(token=token)
    return RoomOut(room_id=await service.add_people_to_room(room_id=data.room_id, data=data))



@router.post("/delete_people_to_room", summary="Удаление участника/ов из комнаты", response_model=RoomOut)
async def delete_people_to_room(token: str,
    data: AddToRoomIn, service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> RoomOut:
    await service_auth.get_current_user(token=token)
    return RoomOut(room_id=await service.delete_people_to_room(room_id=data.room_id, data=data))




# TODO: юзер создающий команду должен быть в data: CreateTeamIn, 
# с определением role и tag, и статусом is_сhief
@router.post("/create_team", summary="Создание комнаты", response_model=list)
async def create_team(token: str,
    data: CreateTeamIn, service: RoomTeamServices = Depends(get_team_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> RoomOut:
    await service_auth.get_current_user(token=token)
    return await service.create_team(data=data)
