from dataclasses import dataclass
import uuid
from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession
from main.db.models.teams import Team 
from main.db.models.rooms import Room 
from main.db.models.users_to_rooms import UsersToRooms
from main.schemas.team_management import CreateRoomIn, AddToRoomIn, UsersList

@dataclass
class RoomTeamRepository:
    db: AsyncSession

    async def create_room(self, data: dict, user_id: str) -> str | None:
        stmt = Room(name = data.name,
                    list_role = data.list_role,
                    list_tag = data.list_tag)
        self.db.add(stmt)
        await self.db.commit()
        await self.db.refresh(stmt)
        
        if stmt.room_id:
            await self._write_users_to_rooms(user_id=user_id, room_id=stmt.room_id)
        else:
            return None
        
    
    async def _write_users_to_rooms(self, user_id: str, room_id: str) -> None:
        stmt = insert(UsersToRooms).values([
        {"user_id": user_id, "room_id": room_id}
        ])
        await self.db.execute(stmt)
        await self.db.commit()
        return room_id
    
    async def check_room(self, room_id):
        stmt = select(Room).where(Room.room_id == room_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

        
    async def add_people_to_room(self, room_id: str, data: list[UsersList]):   
        stmt = insert(UsersToRooms).values(
        [{"user_id": uid.user_id, "room_id": room_id} for uid in data]
        )
        await self.db.execute(stmt)
        await self.db.commit()
        return room_id

    async def delete_people_to_room(self, room_id: str, data: list[UsersList]):
        list_users = [uid.user_id for uid in data]
        stmt = (
            delete(UsersToRooms)
            .where(
            UsersToRooms.room_id == room_id,
            UsersToRooms.user_id.in_(list_users)
            )
        )   

        await self.db.execute(stmt)
        await self.db.commit()
        return room_id
    


    async def create_team(self, room_id, name, data):
        values = [
        {
            "user_id": uid.user_id,
            "room_id": room_id,
            "name": name,
            "role": uid.role,
            "tag": uid.tag,
            "is_chief": uid.is_chief,
        }
        for uid in data
        ]

        stmt = insert(Team).values(values).returning(Team.team_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return [row.team_id for row in result.fetchall()]
            

        