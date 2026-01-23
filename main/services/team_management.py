from typing import Annotated
from uuid import UUID
from main.repositories.team_management import RoomTeamRepository

from fastapi import HTTPException, status, Depends
from main.schemas.team_management import CreateRoomIn, AddToRoomIn
from dataclasses import dataclass



@dataclass
class RoomTeamServices:
    repository: RoomTeamRepository

    async def create_room(self, user_id: str, data: CreateRoomIn) -> str:
        if (result := await self.repository.create_room(user_id=user_id, data=data)):
            return result
        else:
            return HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Комната не создалась"
                )
        
    async def add_people_to_room(self, room_id: UUID, data: AddToRoomIn) -> str:
        if not (await self.repository.check_room(room_id=room_id)):
            return HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена"
                )
        if (result := await self.repository.add_people_to_room(room_id=room_id, data=data.list_users)):
            return result
        else:
            return HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Пользователи не добавились"
                )
        
# TODO: добавить удаление участника/ов и из команд лежащих в комнате
    async def delete_people_to_room(self, room_id: UUID, data: AddToRoomIn) -> str:
        if not (await self.repository.check_room(room_id=room_id)):
            return HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена"
                )
        if (result := await self.repository.delete_people_to_room(room_id=room_id, data=data.list_users)):
            return result



    async def create_team(self, data):
        return await self.repository.create_team(room_id=data.room_id, name=data.name, data=data.list_users)
