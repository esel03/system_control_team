from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from main.db.models.rooms import Room
from main.db.models.teams import TeamMember
from main.db.models.teams_to_rooms import TeamToRoom
from main.db.models.users import User
from main.db.models.users_to_rooms import UsersToRooms
from main.schemas.team_management import RoomMemberIn, TeamMemberIn


@dataclass
class RoomTeamRepository:
    db: AsyncSession

    async def room_exists(self, room_id: UUID) -> bool:
        result = await self.db.execute(select(exists().where(Room.room_id == room_id)))
        return bool(result.scalar())

    async def team_exists(self, team_id: UUID) -> bool:
        result = await self.db.execute(
            select(exists().where(TeamToRoom.team_id == team_id))
        )
        return bool(result.scalar())

    async def active_user_ids(self, user_ids: set[UUID]) -> set[UUID]:
        if not user_ids:
            return set()
        result = await self.db.execute(
            select(User.user_id).where(
                User.user_id.in_(user_ids),
                User.is_deleted.is_(False),
            )
        )
        return set(result.scalars().all())

    async def is_room_member(self, user_id: UUID, room_id: UUID) -> bool:
        result = await self.db.execute(
            select(
                exists().where(
                    UsersToRooms.user_id == user_id,
                    UsersToRooms.room_id == room_id,
                )
            )
        )
        return bool(result.scalar())

    async def is_room_chief(self, user_id: UUID, room_id: UUID) -> bool:
        result = await self.db.execute(
            select(
                exists().where(
                    UsersToRooms.user_id == user_id,
                    UsersToRooms.room_id == room_id,
                    UsersToRooms.is_chief.is_(True),
                )
            )
        )
        return bool(result.scalar())

    async def is_team_member(self, user_id: UUID, team_id: UUID) -> bool:
        result = await self.db.execute(
            select(
                exists().where(
                    TeamMember.user_id == user_id,
                    TeamMember.team_id == team_id,
                )
            )
        )
        return bool(result.scalar())

    async def is_team_chief(self, user_id: UUID, team_id: UUID) -> bool:
        result = await self.db.execute(
            select(
                exists().where(
                    TeamMember.user_id == user_id,
                    TeamMember.team_id == team_id,
                    TeamMember.is_chief.is_(True),
                )
            )
        )
        return bool(result.scalar())

    async def get_room_id_for_team(self, team_id: UUID) -> UUID | None:
        result = await self.db.execute(
            select(TeamToRoom.room_id).where(TeamToRoom.team_id == team_id)
        )
        return result.scalar_one_or_none()

    async def create_room(self, name: str, owner_id: UUID) -> UUID:
        room = Room(name=name)
        self.db.add(room)
        await self.db.flush()
        self.db.add(
            UsersToRooms(
                room_id=room.room_id,
                user_id=owner_id,
                is_chief=True,
            )
        )
        await self.db.flush()
        return room.room_id

    async def add_room_members(
        self,
        room_id: UUID,
        members: list[RoomMemberIn],
    ) -> int:
        values = [
            {
                "user_id": member.user_id,
                "room_id": room_id,
                "is_chief": member.is_chief,
            }
            for member in members
        ]
        stmt = (
            pg_insert(UsersToRooms)
            .values(values)
            .on_conflict_do_nothing(index_elements=["user_id", "room_id"])
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount or 0

    async def room_chief_ids(self, room_id: UUID) -> set[UUID]:
        result = await self.db.execute(
            select(UsersToRooms.user_id).where(
                UsersToRooms.room_id == room_id,
                UsersToRooms.is_chief.is_(True),
            )
        )
        return set(result.scalars().all())

    async def remove_room_members(
        self,
        room_id: UUID,
        user_ids: set[UUID],
    ) -> int:
        team_ids = select(TeamToRoom.team_id).where(TeamToRoom.room_id == room_id)
        await self.db.execute(
            delete(TeamMember).where(
                TeamMember.team_id.in_(team_ids),
                TeamMember.user_id.in_(user_ids),
            )
        )
        result = await self.db.execute(
            delete(UsersToRooms).where(
                UsersToRooms.room_id == room_id,
                UsersToRooms.user_id.in_(user_ids),
            )
        )
        await self.db.flush()
        return result.rowcount or 0

    async def create_team(
        self,
        room_id: UUID,
        name: str,
        owner_id: UUID,
    ) -> UUID:
        team = TeamToRoom(room_id=room_id, name=name)
        self.db.add(team)
        await self.db.flush()
        self.db.add(
            TeamMember(
                team_id=team.team_id,
                user_id=owner_id,
                role="руководитель",
                tag="управление",
                is_chief=True,
            )
        )
        await self.db.flush()
        return team.team_id

    async def add_team_members(
        self,
        team_id: UUID,
        members: list[TeamMemberIn],
    ) -> int:
        values = [
            {
                "team_id": team_id,
                "user_id": member.user_id,
                "role": member.role,
                "tag": member.tag,
                "is_chief": member.is_chief,
            }
            for member in members
        ]
        stmt = (
            pg_insert(TeamMember)
            .values(values)
            .on_conflict_do_nothing(index_elements=["team_id", "user_id"])
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount or 0

    async def team_chief_ids(self, team_id: UUID) -> set[UUID]:
        result = await self.db.execute(
            select(TeamMember.user_id).where(
                TeamMember.team_id == team_id,
                TeamMember.is_chief.is_(True),
            )
        )
        return set(result.scalars().all())

    async def remove_team_members(
        self,
        team_id: UUID,
        user_ids: set[UUID],
    ) -> int:
        result = await self.db.execute(
            delete(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id.in_(user_ids),
            )
        )
        await self.db.flush()
        return result.rowcount or 0

    async def users_in_room(
        self,
        room_id: UUID,
        user_ids: set[UUID],
    ) -> set[UUID]:
        if not user_ids:
            return set()
        result = await self.db.execute(
            select(UsersToRooms.user_id).where(
                UsersToRooms.room_id == room_id,
                UsersToRooms.user_id.in_(user_ids),
            )
        )
        return set(result.scalars().all())

    async def get_rooms_for_user(self, user_id: UUID) -> list[dict]:
        result = await self.db.execute(
            select(Room.room_id, Room.name)
            .join(UsersToRooms, UsersToRooms.room_id == Room.room_id)
            .where(UsersToRooms.user_id == user_id)
            .order_by(Room.name, Room.room_id)
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_teams_for_user(
        self,
        user_id: UUID,
        room_id: UUID,
        include_all: bool,
    ) -> list[dict]:
        stmt = select(TeamToRoom.team_id, TeamToRoom.name).where(
            TeamToRoom.room_id == room_id
        )
        if not include_all:
            stmt = stmt.join(
                TeamMember,
                TeamMember.team_id == TeamToRoom.team_id,
            ).where(TeamMember.user_id == user_id)
        result = await self.db.execute(stmt.order_by(TeamToRoom.name))
        return [dict(row) for row in result.mappings().all()]

    async def get_room_members(self, room_id: UUID) -> list[dict]:
        result = await self.db.execute(
            select(
                User.user_id,
                User.email,
                User.last_name,
                User.first_name,
                User.patronymic_name,
                UsersToRooms.is_chief,
            )
            .join(UsersToRooms, User.user_id == UsersToRooms.user_id)
            .where(
                UsersToRooms.room_id == room_id,
                User.is_deleted.is_(False),
            )
            .order_by(User.last_name, User.first_name)
        )
        return [dict(row) for row in result.mappings().all()]

    async def get_team_members(self, team_id: UUID) -> list[dict]:
        result = await self.db.execute(
            select(
                User.user_id,
                User.email,
                User.last_name,
                User.first_name,
                User.patronymic_name,
                TeamMember.is_chief,
                TeamMember.role,
                TeamMember.tag,
            )
            .join(TeamMember, User.user_id == TeamMember.user_id)
            .where(
                TeamMember.team_id == team_id,
                User.is_deleted.is_(False),
            )
            .order_by(User.last_name, User.first_name)
        )
        return [dict(row) for row in result.mappings().all()]
