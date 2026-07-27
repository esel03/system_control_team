from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from main.db.models.tasks import Status, Task
from main.db.models.teams import TeamMember
from main.db.models.teams_to_rooms import TeamToRoom
from main.db.models.users import User
from main.schemas.tasks import TaskCreate

OPEN_STATUSES = (Status.unassigned, Status.assigned, Status.in_progress)


@dataclass
class TaskRepository:
    db: AsyncSession

    async def get_task(self, task_id: UUID) -> Task | None:
        result = await self.db.execute(
            select(Task).where(
                Task.task_id == task_id,
                Task.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def check_user_exists(self, user_id: UUID) -> bool:
        result = await self.db.execute(
            select(
                exists().where(
                    User.user_id == user_id,
                    User.is_deleted.is_(False),
                )
            )
        )
        return bool(result.scalar())

    async def check_team_exists(self, team_id: UUID) -> bool:
        result = await self.db.execute(
            select(exists().where(TeamToRoom.team_id == team_id))
        )
        return bool(result.scalar())

    async def check_user_is_chief(self, user_id: UUID, team_id: UUID) -> bool:
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

    async def check_user_in_team(self, user_id: UUID, team_id: UUID) -> bool:
        result = await self.db.execute(
            select(
                exists().where(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id,
                )
            )
        )
        return bool(result.scalar())

    async def check_user_is_task_creator(
        self,
        user_id: UUID,
        task_id: UUID,
    ) -> bool:
        result = await self.db.execute(
            select(
                exists().where(
                    Task.task_id == task_id,
                    Task.author == user_id,
                    Task.deleted_at.is_(None),
                )
            )
        )
        return bool(result.scalar())

    async def create_task(
        self,
        data: TaskCreate,
        team_id: UUID,
        author_id: UUID,
        task_status: Status,
        now: datetime,
    ) -> UUID:
        task = Task(
            team_id=team_id,
            task_name=data.task_name,
            task_text=data.task_text,
            author=author_id,
            executor=data.executor,
            priority=data.priority,
            status=task_status,
            difficulty=data.difficulty,
            task_create_date=now,
            task_update_author=author_id,
            task_deadline_date=data.task_deadline_date,
        )
        self.db.add(task)
        await self.db.flush()
        return task.task_id

    async def update_task(
        self,
        task: Task,
        updated_data: dict,
        author_id: UUID,
        now: datetime,
    ) -> UUID:
        if "executor" in updated_data and updated_data["executor"] != task.executor:
            updated_data["last_executor"] = task.executor
        updated_data["task_update_date"] = now
        updated_data["task_update_author"] = author_id
        await self.db.execute(
            update(Task)
            .where(
                Task.task_id == task.task_id,
                Task.deleted_at.is_(None),
            )
            .values(**updated_data)
        )
        await self.db.flush()
        return task.task_id

    async def soft_delete_task(
        self,
        task_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> bool:
        result = await self.db.execute(
            update(Task)
            .where(
                Task.task_id == task_id,
                Task.deleted_at.is_(None),
            )
            .values(deleted_at=now, deleted_by=actor_id)
        )
        await self.db.flush()
        return bool(result.rowcount)

    async def complete_task(
        self,
        task_id: UUID,
        actor_id: UUID,
        now: datetime,
    ) -> bool:
        result = await self.db.execute(
            update(Task)
            .where(
                Task.task_id == task_id,
                Task.deleted_at.is_(None),
                Task.status.in_(OPEN_STATUSES),
            )
            .values(
                status=Status.completed,
                task_finish_date=now,
                task_update_date=now,
                task_update_author=actor_id,
            )
        )
        await self.db.flush()
        return bool(result.rowcount)

    async def get_team_tasks(
        self,
        team_id: UUID,
        task_status: Status | None,
        start_date: datetime,
        end_date: datetime,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        filters = [
            Task.team_id == team_id,
            Task.deleted_at.is_(None),
        ]
        if task_status is not None:
            filters.append(Task.status == task_status)
        if task_status == Status.completed:
            filters.extend(
                [
                    Task.task_finish_date >= start_date,
                    Task.task_finish_date <= end_date,
                ]
            )
        return await self._get_tasks(filters, limit, offset)

    async def get_user_tasks(
        self,
        team_id: UUID,
        user_id: UUID,
        task_status: Status | None,
        start_date: datetime,
        end_date: datetime,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        filters = [
            Task.team_id == team_id,
            Task.executor == user_id,
            Task.deleted_at.is_(None),
        ]
        if task_status is not None:
            filters.append(Task.status == task_status)
        if task_status == Status.completed:
            filters.extend(
                [
                    Task.task_finish_date >= start_date,
                    Task.task_finish_date <= end_date,
                ]
            )
        return await self._get_tasks(filters, limit, offset)

    async def _get_tasks(
        self,
        filters: list,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        result = await self.db.execute(
            select(Task)
            .where(*filters)
            .order_by(Task.task_create_date.desc(), Task.task_id)
            .limit(limit)
            .offset(offset)
        )
        total_result = await self.db.execute(
            select(func.count(Task.task_id)).where(*filters)
        )
        return list(result.scalars().all()), int(total_result.scalar() or 0)

    async def count_user_completed_tasks(
        self,
        team_id: UUID,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        return await self._count_tasks(
            Task.team_id == team_id,
            Task.executor == user_id,
            Task.status == Status.completed,
            Task.deleted_at.is_(None),
            Task.task_finish_date.between(start_date, end_date),
        )

    async def count_user_in_progress_tasks(
        self,
        team_id: UUID,
        user_id: UUID,
    ) -> int:
        return await self._count_tasks(
            Task.team_id == team_id,
            Task.executor == user_id,
            Task.status.in_(OPEN_STATUSES),
            Task.deleted_at.is_(None),
        )

    async def count_team_completed_tasks(
        self,
        team_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        return await self._count_tasks(
            Task.team_id == team_id,
            Task.status == Status.completed,
            Task.deleted_at.is_(None),
            Task.task_finish_date.between(start_date, end_date),
        )

    async def count_team_in_progress_tasks(self, team_id: UUID) -> int:
        return await self._count_tasks(
            Task.team_id == team_id,
            Task.status.in_(OPEN_STATUSES),
            Task.deleted_at.is_(None),
        )

    async def _count_tasks(self, *filters) -> int:
        result = await self.db.execute(select(func.count(Task.task_id)).where(*filters))
        return int(result.scalar() or 0)
