from uuid import UUID
from main.repositories.team_management import RoomTeamRepository

from fastapi import HTTPException, status
from main.schemas.team_management import (
    AddToTeamIn,
    DeleteTeamPeople,
    DeleteRoomPeople,
    CreateRoomOut,
    UserListRoom,
    UsersList,
    AddToTeamOut,
)
from dataclasses import dataclass


@dataclass
class RoomTeamServices:
    repository: RoomTeamRepository

    async def access_right_user_in_room(self, user_id: UUID, room_id: UUID) -> bool:
        """
        Функция проверяет права пользователя на комнату (is_chief)
        Если is_chief == True, то пользователь может работать* с комнатой
        Работать - добавлять участников, удалять участников

        Если is_chief == True -> вернется True
        """

        if not (
            await self.repository.get_info_about_user_in_room(
                user_id=user_id, room_id=room_id
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Нет достаточных прав на комнату",
            )
        return True

    async def access_right_user_in_team(self, user_id: UUID, team_id: UUID) -> bool:
        """
        Функция проверяет права пользователя на команду (is_chief)
        Если is_chief == True, то пользователь может работать* с командой
        Работать - добавлять участников, удалять участников

        Если is_chief == True -> вернется True
        """
        if not (
            await self.repository.get_info_about_user_in_team(
                user_id=user_id, team_id=team_id
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Нет достаточных прав на команду",
            )
        return True

    # создание комнаты
    async def create_room(self, user_id: UUID, name: str) -> UUID:
        """
        Создается комната
        data: name -> str, user_id -> UUID
        return: room_id -> UUID, user_id -> UUID

        Функция проходит в два действия:
            1) создается комната, возвращает room_id
            2) добавляется один пользователь, который создает
        """
        if result := await self.repository.create_room(name=name):
            values = [UserListRoom(user_id=user_id, is_chief=True)]
            if (
                await self.repository.write_users_to_room_safe(
                    data=values, room_id=result
                )
                == True
            ):
                return CreateRoomOut(room_id=result)
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Комната не создалась, попробуйте еще раз",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Комната не создалась"
            )

    # добавление участников в комнату
    async def add_people_to_room(
        self, room_id: UUID, data: list[UserListRoom]
    ) -> UUID | None:
        """
        Функция добавляет участников в комнату,
        Добавляются только те участники, которых нет в комнате,
        а те которые там уже есть - не добавляются (ошибка не возникает!)
        "вдавливаются" в базу данных мягко
        in: room_id -> UUID, data -> room_id: UUID, list_users: list[user_id: UUID, is_chief: bool = False]
        return: room_id -> UUID
        """
        if await self.repository.write_users_to_room_safe(room_id=room_id, data=data):
            return room_id
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователи не добавились в комнату",
            )

    # удаление участника/ов из комнаты и из команд лежащих в комнате
    async def delete_people_to_room(self, room_id: UUID, data: DeleteRoomPeople) -> str:
        if not (await self.repository.check_room(room_id=room_id)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена"
            )

        if result := await self.repository.delete_people_to_room(
            room_id=room_id, data=data.list_users
        ):
            return result

    # создание команды
    async def create_team(self, user_id: UUID, room_id: UUID, name: str):
        if not (result := await self.repository.create_team(room_id=room_id)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Команда не создана"
            )
        return await self.repository._write_users_to_teams(
            team_id=result,
            room_id=room_id,
            name=name,
            data=[UsersList(user_id=user_id, is_chief=True)],
        )

    # добавление участников в команду
    async def add_people_to_team(self, user_id: UUID, data: AddToTeamIn) -> UUID:
        room_id = await self.repository.get_room_on_team(team_id=data.team_id)

        values = [uid.user_id for uid in data.list_users]

        amount = await self.repository.are_users_in_room(room_id=room_id, data=values)
        if amount.existing_user_id >= amount.in_data:
            await self.repository._write_users_to_teams(
                team_id=data.team_id,
                room_id=room_id,
                name=data.name,
                data=data.list_users,
            )
            return AddToTeamOut(team_id=data.team_id, list_users=values)
        else:

            result_list_no_room = [
                uid for uid in (amount.in_data - amount.existing_user_id)
            ]  # список юзеров, которых нет в комнате

            # проверка на права юзера на комнату
            if (
                await self.repository.get_info_about_user_in_room(
                    user_id=user_id, room_id=room_id
                )
                == True
            ):
                await self.add_people_to_room(
                    room_id=room_id,
                    data=[
                        UserListRoom(user_id=uid, is_chief=False)
                        for uid in result_list_no_room
                    ],
                )
                await self.repository._write_users_to_teams(
                    team_id=data.team_id,
                    room_id=room_id,
                    name=data.name,
                    data=data.list_users,
                )
                return AddToTeamOut(team_id=data.team_id, list_users=values)
            else:
                result_list = [
                    uid for uid in amount.existing_user_id
                ]  # список юзеров, которые есть в комнате
                if not result_list:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Отсутствуют права на добавление некоторых пользователей в комнату, и соответственно - в команду",
                    )
                input_value = []
                for elem in data.list_users:
                    if elem.user_id in result_list:
                        input_value.append(elem)

                await self.repository._write_users_to_teams(
                    team_id=data.team_id,
                    room_id=room_id,
                    name=data.name,
                    data=input_value,
                )
                return AddToTeamOut(team_id=data.team_id, list_users=result_list)

    # удаление участника/ов из команд
    async def delete_people_to_team(self, data: DeleteTeamPeople) -> UUID:
        return await self.repository.delete_people_of_team(
            team_id=data.team_id, data=data.list_users
        )

    # получение списка комнат юзера
    async def get_list_rooms(self, user_id: UUID):
        result = await self.repository.get_list_rooms(user_id=user_id)
        return {"list_rooms": [dict(row) for row in result]}

    # получение списка команд юзера
    async def get_list_teams(self, user_id: UUID, room_id: UUID):
        if not (await self.repository.check_room(room_id=room_id)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена"
            )
        if await self.repository.get_info_about_user_in_room(
            user_id=user_id, room_id=room_id
        ):
            result = await self.repository.get_list_teams_not_user(room_id=room_id)
        else:
            result = await self.repository.get_list_teams(
                user_id=user_id, room_id=room_id
            )
        return {"list_teams": [dict(row) for row in result]}

    # получение списка юзеров в комнате
    async def get_list_users_rooms(self, room_id: UUID):
        result = await self.repository._get_list_users_to_rooms(room_id=room_id)
        return {"list_users": [dict(row) for row in result]}

    async def get_list_users_teams(self, team_id: UUID):
        result = await self.repository._get_list_users_to_teams(team_id=team_id)
        return {"list_users": [dict(row) for row in result]}
