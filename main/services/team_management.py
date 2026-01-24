from uuid import UUID
from main.repositories.team_management import RoomTeamRepository

from fastapi import HTTPException, status, Depends
from main.schemas.team_management import CreateRoomIn, AddToRoomIn, CreateTeamIn, AddToTeamIn, DeleteTeamPeople, DeleteRoomPeople
from dataclasses import dataclass


@dataclass
class RoomTeamServices:
    repository: RoomTeamRepository

    # создание комнаты
    async def create_room(self, data: CreateRoomIn) -> str:
        if result := await self.repository.create_room(data=data):
            values = []
            for user in data.list_users:
                values.append(user.user_id)
            return await self.repository._write_users_to_rooms(
                data=values, room_id=result
            )
        else:
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Комната не создалась"
            )

    # добавление участников в комнату
    async def add_people_to_room(self, room_id: UUID, data: AddToRoomIn) -> UUID | None:
        if not (await self.repository.check_room(room_id=room_id)):
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена"
            )
        if list_users_to_add := await self._matched_users(
            room_id=room_id, list_users=data.list_users
        ):
            if result := await self.repository._write_users_to_rooms(
                room_id=room_id, data=list_users_to_add
            ):
                return result
            else:
                return HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Пользователи не добавились в комнату",
                )
        return None

    # сравнение списков пользователей и комнаты
    async def _matched_users(
        self, room_id: UUID, list_users: list
    ) -> list[UUID] | None:
        values = set()
        for user in list_users:
            values.add(user.user_id)

        if not (
            result_set := values
            - set(await self.repository._get_list_users_to_rooms(room_id=room_id))
        ):
            return None
        return list(result_set)
        
    
        
    # удаление участника/ов из комнаты и из команд лежащих в комнате
    async def delete_people_to_room(self, room_id: UUID, data: DeleteRoomPeople) -> str:
        if not (await self.repository.check_room(room_id=room_id)):
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена"
            )
        
        if result := await self.repository.delete_people_to_room(
            room_id=room_id, data=data.list_users
        ):
            return result

    # создание команды
    async def create_team(self, data: CreateTeamIn):
        await self.add_people_to_room(room_id=data.room_id, data=data)
        
        if not (result := await self.repository.create_team(data=data)):
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Команда не создана"
            )
        return await self.repository._write_users_to_teams(
            team_id=result, room_id=data.room_id, name=data.name, data=data.list_users
        )

    # добавление участников в команду
    async def add_people_to_team(self, data: AddToTeamIn) -> UUID:
        if not (result := await self.repository.get_room_on_team(team_id=data.team_id)):
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Команда не найдена"
            )
        await self.add_people_to_room(room_id=result, data=data)
        return await self.repository._write_users_to_teams(team_id=data.team_id, room_id=result, name=data.name, data=data.list_users)

    # удаление участника/ов из команд
    async def delete_people_to_team(self, data: DeleteTeamPeople) -> UUID:
        return await self.repository.delete_people_of_team(team_id=data.team_id, data=data.list_users)
    
    # получение списка комнат юзера
    async def get_list_rooms(self, user_id: UUID):
        result = await self.repository.get_list_rooms(user_id=user_id)
        return {"list_room_id": [id for id in result]}
    
# TODO: завтра доделать)

    #async def get_list_users_in_rooms(self, room_id: UUID):
    #    result = await self.repository._get_list_users_to_rooms(room_id=room_id)
    #    return 
    
    #async def get_list_teams(self, user_id: UUID):
