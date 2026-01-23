from dataclasses import dataclass
from uuid import UUID
from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession
from main.db.models.teams import Team
from main.db.models.rooms import Room
from main.db.models.users_to_rooms import UsersToRooms
from main.db.models.teams_to_rooms import TeamToRoom
from main.schemas.team_management import CreateRoomIn, AddToRoomIn, UsersList, CreateTeamIn, AddToTeamIn

@dataclass
class RoomTeamRepository:
    db: AsyncSession

    # создает комнату и возвращает ее id
    async def create_room(self, data: dict) -> UUID | None:
        stmt = Room(name = data.name,
                    list_role = data.list_role,
                    list_tag = data.list_tag)
        self.db.add(stmt)
        await self.db.commit()
        await self.db.refresh(stmt)
        return stmt.room_id
    
        
    # отдает список пользователей комнаты
    async def _get_list_users_to_rooms(self, room_id: UUID) -> set:
        stmt = (select(UsersToRooms.user_id)
                .where(Room.room_id == room_id))
        list_users_to_rooms = await self.db.execute(stmt)
        result = list_users_to_rooms.scalars().all()
        return set(result)
            

    # записывает пользователей в комнату
    async def _write_users_to_rooms(self, data: list[UUID], room_id: UUID) -> UUID:
        stmt = insert(UsersToRooms).values(
            [{"user_id": uid, "room_id": room_id} for uid in data]
        )
        await self.db.execute(stmt)
        await self.db.commit()
        return room_id
    
    # проверяет существование комнаты
    async def check_room(self, room_id):
        stmt = select(Room).where(Room.room_id == room_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # удаляет участников из комнаты
    async def delete_people_to_room(self, room_id: str, data: list[UsersList]):
        list_users = [uid.user_id for uid in data]
        stmt = delete(UsersToRooms).where(
            UsersToRooms.room_id == room_id, UsersToRooms.user_id.in_(list_users)
        )

        await self.db.execute(stmt)
        await self.db.commit()
        return room_id
    

    # создает команду
    async def create_team(self, data: CreateTeamIn)-> UUID | None:
        stmt = TeamToRoom(room_id = data.room_id)
        self.db.add(stmt)
        await self.db.commit()
        await self.db.refresh(stmt)
        return stmt.team_id
    
    # записывает/добавляет пользователей в команду
    async def _write_users_to_teams(self, team_id: UUID, room_id: UUID, name: str, data: UsersList) -> UUID:
        stmt = insert(Team).values(
            [{"team_id": team_id, 
              "room_id": room_id,
              "user_id": uid.user_id,
              "name": name,
              "role": uid.role,
              "tag": uid.tag,
              "is_chief": uid.is_chief} 
              for uid in data]
        )
        await self.db.execute(stmt)
        await self.db.commit()
        return team_id
    

    # отдает гуид комнаты по команде
    async def get_room_on_team(self, team_id: UUID) -> UUID | None:
        stmt = (select(TeamToRoom.room_id)
                .where(TeamToRoom.team_id == team_id))
        room_id = await self.db.execute(stmt)
        return room_id.scalar_one_or_none()
        
          

        
