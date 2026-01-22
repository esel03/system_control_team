from typing import Annotated
from uuid import UUID
from main.repositories.team_management import RoomTeamRepository

from fastapi import HTTPException, status, Depends
from main.schemas.team_management import RoomOut,  CreateRoomIn
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
