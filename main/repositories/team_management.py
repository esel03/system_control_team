from dataclasses import dataclass
from uuid import UUID
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession
from main.db.models.teams import Team
from main.db.models.rooms import Room
from main.db.models.users_to_rooms import UsersToRooms
from main.db.models.teams_to_rooms import TeamToRoom
from main.schemas.team_management import CreateRoomIn, AddToRoomIn, UsersList, CreateTeamIn, AddToTeamIn, UserListRoom, NumUsId

@dataclass
class RoomTeamRepository:
    db: AsyncSession

    # создает комнату и возвращает ее id
    async def create_room(self, name: str) -> UUID | None:
        stmt = Room(name = name)
        self.db.add(stmt)
        await self.db.commit()
        await self.db.refresh(stmt)
        return stmt.room_id

    # отдает список пользователей комнаты
    async def _get_list_users_to_rooms(self, room_id: UUID) -> set[UUID]:
        stmt = (select(UsersToRooms.user_id)
                .where(Room.room_id == room_id))
        list_users_to_rooms = await self.db.execute(stmt)
        result = list_users_to_rooms.scalars().all()
        return set(result)
    
            

    # записывает пользователей в комнату
    async def _write_users_to_rooms(self, data: list[UserListRoom], room_id: UUID) -> bool:
        stmt = insert(UsersToRooms).values(
            [{"user_id": uid.user_id, "room_id": room_id, "is_chief": uid.is_chief} for uid in data]
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        if result.rowcount > 0:
            return True
        return False
    
    # проверяет существование комнаты
    async def check_room(self, room_id: UUID):
        stmt = select(Room).where(Room.room_id == room_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # удаляет участников из комнаты, соответсвенно из команд, в этой комнате
    async def delete_people_to_room(self, room_id: UUID, data: list[UUID]):
        await self.db.execute(
            delete(Team)
            .where(Team.room_id == room_id)
            .where(Team.user_id.in_(data))
        )

        await self.db.execute(
            delete(UsersToRooms)
            .where(UsersToRooms.room_id == room_id)
            .where(UsersToRooms.user_id.in_(data))
        )
        
        await self.db.commit()
        return room_id

    # создает команду
    async def create_team(self, room_id: UUID)-> UUID | None:
        stmt = TeamToRoom(room_id = room_id)
        self.db.add(stmt)
        await self.db.commit()
        await self.db.refresh(stmt)
        return stmt.team_id

    # записывает/добавляет пользователей в команду
    async def _write_users_to_teams(self, team_id: UUID, room_id: UUID, name: str, data: list[UsersList]) -> UUID:
        stmt = (pg_insert(Team).values(
            [{"team_id": team_id, 
              "room_id": room_id,
              "user_id": uid.user_id,
              "name": name,
              "role": uid.role,
              "tag": uid.tag,
              "is_chief": uid.is_chief} 
              for uid in data]
        )
        .on_conflict_do_nothing(index_elements=["user_id", "room_id", "team_id"])
        )
        await self.db.execute(stmt)
        await self.db.commit()
        return team_id

    async def are_users_in_room(self, room_id: UUID, data: list[UUID]) -> NumUsId:
        """
        Проверяет, все ли переданные пользователи находятся в указанной комнате.
        Возвращает True, если все пользователи есть в комнате, иначе False
        """
        stmt = (
            select(UsersToRooms.user_id)
            .where(
                UsersToRooms.room_id == room_id,
                UsersToRooms.user_id.in_(data)
            )
            )

        result = await self.db.execute(stmt)
        existing_user_id = set(result.scalars().all())

        return NumUsId(existing_user_id=existing_user_id, in_data=set(data))
    

    # отдает id комнаты по команде
    async def get_room_on_team(self, team_id: UUID) -> UUID | None:
        stmt = select(TeamToRoom.room_id).where(TeamToRoom.team_id == team_id)
        room_id = await self.db.execute(stmt)
        return room_id.scalar_one_or_none()
    

    # удаляет участников из команды
    async def delete_people_of_team(self, team_id: UUID, data: list[UUID]):
        stmt = (delete(Team)
                .where(Team.team_id == team_id)
                .where(Team.user_id.in_(data)))
        await self.db.execute(stmt)
        await self.db.commit()
        return team_id

    # отдает список комнат, в которых состоит пользователь
    async def get_list_rooms(self, user_id: UUID):
        stmt = (select(UsersToRooms.room_id)
                .where(UsersToRooms.user_id == user_id))
        return (await self.db.execute(stmt)).scalars().all()
    
    # отдает is_chief 
    async def get_info_about_user_in_room(self, user_id: UUID, room_id: UUID) -> bool | None:
        stmt = (select(UsersToRooms.is_chief)
                .where(UsersToRooms.user_id == user_id)
                .where(UsersToRooms.room_id == room_id))
        if (result := (await self.db.execute(stmt)).scalar_one_or_none()):
            if result == True:
                return True
            return None
        return None
    

    async def get_info_about_user_in_team(self, user_id: UUID, team_id: UUID) -> bool | None:
        stmt = (select(Team.is_chief)
                .where(Team.user_id == user_id)
                .where(Team.team_id == team_id))
        if (result := (await self.db.execute(stmt)).scalar_one_or_none()):
            if result == True:
                return True
            return None
        return None
    

    async def write_users_to_room_safe(self, room_id: UUID, data: list[UserListRoom]) -> bool | None:
        '''
        Добавляет пользователей в комнату.
        Если пользователь уже есть — игнорирует, продолжает с остальными.
        '''
        values = [
            {"user_id": param.user_id, "room_id": room_id, "is_chief": param.is_chief}
            for param in data
            ]

        stmt = (
            pg_insert(UsersToRooms)
            .values(values)
            .on_conflict_do_nothing(index_elements=["user_id", "room_id"])
            )

        result = await self.db.execute(stmt)
        await self.db.commit()
        if result.rowcount > 0:
            return True
        return None

        



    # проверяет существование пользователя в команде
    async def check_user_in_team(self, team_id: UUID, user_id: UUID) -> bool:
        stmt = select(Team).where(Team.team_id == team_id, Team.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar() is not None
