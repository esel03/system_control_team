import logging
from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, status

from main.repositories.team_management import RoomTeamRepository
from main.schemas.team_management import (
    RoomMemberIn,
    TeamMemberIn,
)

logger = logging.getLogger(__name__)


@dataclass
class RoomTeamServices:
    repository: RoomTeamRepository

    async def require_room_member(self, user_id: UUID, room_id: UUID) -> None:
        if not await self.repository.room_exists(room_id):
            raise HTTPException(status_code=404, detail="Комната не найдена")
        if not await self.repository.is_room_member(user_id, room_id):
            raise HTTPException(status_code=403, detail="Нет доступа к комнате")

    async def require_room_chief(self, user_id: UUID, room_id: UUID) -> None:
        if not await self.repository.room_exists(room_id):
            raise HTTPException(status_code=404, detail="Комната не найдена")
        if not await self.repository.is_room_chief(user_id, room_id):
            raise HTTPException(
                status_code=403,
                detail="Требуются права руководителя комнаты",
            )

    async def require_team_member(self, user_id: UUID, team_id: UUID) -> None:
        if not await self.repository.team_exists(team_id):
            raise HTTPException(status_code=404, detail="Команда не найдена")
        if not await self.repository.is_team_member(user_id, team_id):
            raise HTTPException(status_code=403, detail="Нет доступа к команде")

    async def require_team_chief(self, user_id: UUID, team_id: UUID) -> None:
        if not await self.repository.team_exists(team_id):
            raise HTTPException(status_code=404, detail="Команда не найдена")
        if not await self.repository.is_team_chief(user_id, team_id):
            raise HTTPException(
                status_code=403,
                detail="Требуются права руководителя команды",
            )

    async def create_room(self, user_id: UUID, name: str) -> UUID:
        room_id = await self.repository.create_room(name, user_id)
        logger.info("room_created actor=%s room=%s", user_id, room_id)
        return room_id

    async def add_room_members(
        self,
        actor_id: UUID,
        room_id: UUID,
        members: list[RoomMemberIn],
    ) -> int:
        await self.require_room_chief(actor_id, room_id)
        members = self._unique_members(members)
        requested = {member.user_id for member in members}
        active = await self.repository.active_user_ids(requested)
        if active != requested:
            raise HTTPException(
                status_code=400,
                detail="Один или несколько пользователей не существуют или удалены",
            )
        added = await self.repository.add_room_members(room_id, members)
        logger.info(
            "room_members_added actor=%s room=%s count=%s",
            actor_id,
            room_id,
            added,
        )
        return added

    async def remove_room_members(
        self,
        actor_id: UUID,
        room_id: UUID,
        user_ids: list[UUID],
    ) -> int:
        await self.require_room_chief(actor_id, room_id)
        targets = set(user_ids)
        chief_ids = await self.repository.room_chief_ids(room_id)
        if chief_ids and not (chief_ids - targets):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя удалить всех руководителей комнаты",
            )
        removed = await self.repository.remove_room_members(room_id, targets)
        logger.info(
            "room_members_removed actor=%s room=%s count=%s",
            actor_id,
            room_id,
            removed,
        )
        return removed

    async def create_team(
        self,
        user_id: UUID,
        room_id: UUID,
        name: str,
    ) -> UUID:
        await self.require_room_chief(user_id, room_id)
        team_id = await self.repository.create_team(room_id, name, user_id)
        logger.info("team_created actor=%s team=%s room=%s", user_id, team_id, room_id)
        return team_id

    async def add_team_members(
        self,
        actor_id: UUID,
        team_id: UUID,
        members: list[TeamMemberIn],
    ) -> int:
        await self.require_team_chief(actor_id, team_id)
        room_id = await self.repository.get_room_id_for_team(team_id)
        if room_id is None:
            raise HTTPException(status_code=404, detail="Команда не найдена")

        members = self._unique_members(members)
        requested = {member.user_id for member in members}
        active = await self.repository.active_user_ids(requested)
        if active != requested:
            raise HTTPException(
                status_code=400,
                detail="Один или несколько пользователей не существуют или удалены",
            )
        in_room = await self.repository.users_in_room(room_id, requested)
        if in_room != requested:
            raise HTTPException(
                status_code=400,
                detail="Сначала добавьте пользователей в комнату",
            )
        added = await self.repository.add_team_members(team_id, members)
        logger.info(
            "team_members_added actor=%s team=%s count=%s",
            actor_id,
            team_id,
            added,
        )
        return added

    async def remove_team_members(
        self,
        actor_id: UUID,
        team_id: UUID,
        user_ids: list[UUID],
    ) -> int:
        await self.require_team_chief(actor_id, team_id)
        targets = set(user_ids)
        chief_ids = await self.repository.team_chief_ids(team_id)
        if chief_ids and not (chief_ids - targets):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя удалить всех руководителей команды",
            )
        removed = await self.repository.remove_team_members(team_id, targets)
        logger.info(
            "team_members_removed actor=%s team=%s count=%s",
            actor_id,
            team_id,
            removed,
        )
        return removed

    async def get_rooms(self, user_id: UUID) -> list[dict]:
        return await self.repository.get_rooms_for_user(user_id)

    async def get_teams(self, user_id: UUID, room_id: UUID) -> list[dict]:
        await self.require_room_member(user_id, room_id)
        include_all = await self.repository.is_room_chief(user_id, room_id)
        return await self.repository.get_teams_for_user(
            user_id,
            room_id,
            include_all,
        )

    async def get_room_members(self, user_id: UUID, room_id: UUID) -> list[dict]:
        await self.require_room_member(user_id, room_id)
        return await self.repository.get_room_members(room_id)

    async def get_team_members(self, user_id: UUID, team_id: UUID) -> list[dict]:
        await self.require_team_member(user_id, team_id)
        return await self.repository.get_team_members(team_id)

    @staticmethod
    def _unique_members(members: list) -> list:
        by_user_id = {member.user_id: member for member in members}
        return list(by_user_id.values())
