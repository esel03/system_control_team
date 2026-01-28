from dataclasses import dataclass
from uuid import UUID
from sqlalchemy import delete, func, select, update, exists
from sqlalchemy.ext.asyncio import AsyncSession
from main.db.models.tasks import Task
from main.db.models.users import User
from main.db.models.teams import Team
from sqlalchemy.exc import SQLAlchemyError

from main.schemas.tasks import TaskCreate, TaskUpdate, ListTasksOut
from datetime import datetime, timezone


@dataclass
class TaskRepository:
    db: AsyncSession

    async def get_task(self, task_id: UUID) -> Task | None:
        """
        Функция получения задачи по id, на вход принимает id задачи возвращает задачу или None
        """
        stmt = select(Task).where(Task.task_id == task_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def check_user_exists(self, user_id: UUID) -> bool | None:
        stmt = select(exists()).where(User.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar()

    async def check_team_exists(self, team_id: UUID) -> bool | None:
        stmt = select(exists()).where(Team.team_id == team_id)
        result = await self.db.execute(stmt)
        return result.scalar()

    async def check_user_is_chief(self, user_id: UUID, team_id: UUID) -> bool:
        stmt = (
            select(Team)
            .where(Team.user_id == user_id)
            .where(Team.is_chief == True)
            .where(Team.team_id == team_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() is not None

    async def check_user_in_team(self, user_id: UUID, team_id: UUID) -> bool:
        stmt = (
            select(Team).where(Team.team_id == team_id).where(Team.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() is not None

    async def check_user_is_task_creator(self, user_id: UUID, task_id: UUID) -> bool:
        stmt = select(Task).where(Task.task_id == task_id).where(Task.author == user_id)
        result = await self.db.execute(stmt)
        return result.scalar() is not None

    async def create_task(self, data: TaskCreate, author_id: UUID) -> UUID:
        """
        Функция создания задачи, на вход принимает id пользователя, возвращает id созданной задачи
        """
        task = Task(
            **data.model_dump(exclude={"author", "executor", "task_finish_date"}),
            author=author_id,
            executor=data.executor,
            task_create_date=datetime.now(timezone.utc),
            task_update_date=None,
            task_update_author=author_id,
            is_completed=False,
            task_deadline_date=data.task_deadline_date,
            task_finish_date=None,
            last_executor=None
        )
        try:
            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)
        except SQLAlchemyError:
            await self.db.rollback()
            raise
        return task.task_id

    async def update_task(
        self, data: TaskUpdate, task_id: UUID, author_id: UUID
    ) -> UUID:
        task = await self.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
        updated_data = data.model_dump(exclude_unset=True, exclude_none=True)
        if not updated_data:
            return task_id
        if "executor" in updated_data:
            if updated_data["executor"] != task.executor:
                updated_data["last_executor"] = task.executor
        updated_data["task_update_date"] = datetime.now(timezone.utc)
        updated_data["task_update_author"] = author_id
        try:
            stmt = update(Task).where(Task.task_id == task_id).values(**updated_data)
            await self.db.execute(stmt)
            await self.db.commit()
            return task_id
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def delete_task(self, task_id: UUID) -> bool:
        task = await self.get_task(task_id)
        if not task:
            return False
        try:
            stmt = delete(Task).where(Task.task_id == task_id)
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def complete_task(self, task_id: UUID, user_id: UUID) -> bool:
        task = await self.get_task(task_id)
        if not task:
            return False
        stmt = (
            update(Task)
            .where(Task.task_id == task_id)
            .where(Task.executor == user_id)
            .where(Task.is_completed.is_(False))
            .values(
                is_completed=True,
                task_finish_date=datetime.now(timezone.utc),
            )
        )
        try:
            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def get_team_tasks(
        self, team_id: UUID, completed: bool, start_date: datetime, end_date: datetime
    ) -> list[ListTasksOut]:
        if completed:
            stmt = (
                select(Task)
                .where(Task.team_id == team_id)
                .where(Task.is_completed == True)
                .where(Task.task_finish_date >= start_date)
                .where(Task.task_finish_date <= end_date)
            )
        else:
            stmt = (
                select(Task)
                .where(Task.team_id == team_id)
                .where(Task.is_completed == False)
            )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_tasks(
        self,
        team_id: UUID,
        user_id: UUID,
        completed: bool,
        start_date: datetime,
        end_date: datetime,
    ) -> list[ListTasksOut]:
        if completed:
            stmt = (
                select(Task)
                .where(Task.team_id == team_id)
                .where(Task.executor == user_id)
                .where(Task.is_completed == True)
                .where(Task.task_finish_date >= start_date)
                .where(Task.task_finish_date <= end_date)
            )
        else:
            stmt = (
                select(Task)
                .where(Task.team_id == team_id)
                .where(Task.executor == user_id)
                .where(Task.is_completed == False)
            )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_user_completed_tasks(
        self, team_id: UUID, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> int:
        stmt = (
            select(func.count(Task.task_id))
            .where(Task.team_id == team_id)
            .where(Task.executor == user_id)
            .where(Task.is_completed == True)
            .where(Task.task_finish_date >= start_date)
            .where(Task.task_finish_date <= end_date)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_user_in_progress_tasks(self, team_id: UUID, user_id: UUID) -> int:
        stmt = (
            select(func.count(Task.task_id))
            .where(Task.team_id == team_id)
            .where(Task.executor == user_id)
            .where(Task.is_completed == False)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_team_completed_tasks(
        self, team_id: UUID, start_date: datetime, end_date: datetime
    ) -> int:
        stmt = select(func.count(Task.task_id)).where(
            Task.team_id == team_id,
            Task.is_completed.is_(True),
            Task.task_finish_date.between(start_date, end_date),
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def count_team_in_progress_tasks(self, team_id: UUID) -> int:
        stmt = select(func.count(Task.task_id)).where(
            Task.team_id == team_id, Task.is_completed.is_(False)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
