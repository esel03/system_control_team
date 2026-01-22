from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from main.db.models.users import User 
from main.db.models.rooms import Room 
from main.db.models.users_to_rooms import UsersToRooms

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
        print('TEST=====\n', type(str(stmt.room_id)), stmt.room_id)
        print('TEST=====\n', type(str(user_id)), user_id)
        #return stmt.room_id
        
        if stmt.room_id:
            
            query = UsersToRooms(
                user_id = str(user_id),
                room_id = str(stmt.room_id),
            )
            self.db.add(query)
            await self.db.commit()
            return stmt.room_id
        else:
            return None
            

        