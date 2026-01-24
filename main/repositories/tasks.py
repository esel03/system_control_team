from dataclasses import dataclass
import uuid
from sqlalchemy import delete, or_, and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from main.db.models.tasks import Task
from main.db.models.teams import Team
from main.db.models.teams_to_rooms import TeamToRoom
from main.schemas.tasks import TaskCreate, TaskUpdate
from datetime import datetime, timezone


@dataclass
class TaskRepository:
    db: AsyncSession

    async def get_task_for_view(self, task_id: uuid.UUID) -> Task | None:
        """
        функция для получения задачи по id
        """
        stmt = select(Task).where(Task.task_id == task_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_task_for_action(
        self, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> Task | None:
        """
        Возвращает задачу, если пользователь:
        является автором задачи или шефом команды.
        """
        stmt = (
            select(Task)
            .join(TeamToRoom, Task.team_id == TeamToRoom.team_id)
            .join(Team, TeamToRoom.team_id == Team.team_id)
            .where(Task.task_id == task_id)
            .where(
                or_(
                    Task.author == user_id,
                    and_(Team.user_id == user_id, Team.is_chief == True),
                )
            )
            .distinct(Task.task_id)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_task(self, data: TaskCreate, author_id: uuid.UUID) -> uuid.UUID:
        """
        функция для создания задачи, возвращает id созданной задачи
        """
        stmt = Task(
            **data.model_dump(),
            author=author_id,
            task_create_date=datetime.now(timezone.utc),
            task_update_date=None
        )
        self.db.add(stmt)
        await self.db.commit()
        await self.db.refresh(stmt)
        return stmt.task_id

    async def update_task(
        self, task_id: uuid.UUID, user_id: uuid.UUID, data: TaskUpdate
    ) -> uuid.UUID | None:
        """
        функция обновления задачи по ID.
        """
        task = await self.get_task_for_action(task_id, user_id)
        if not task:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            update_data = {}
        if "executor" in update_data and update_data["executor"] != task.executor:
            update_data["last_executor"] = task.executor
        update_data["task_update_date"] = datetime.now(timezone.utc)
        update_data["task_update_author"] = user_id
        stmt = update(Task).where(Task.task_id == task_id).values(**update_data)
        result = await self.db.execute(stmt)
        if result.rowcount == 0:
            return None
        await self.db.commit()
        return task_id

    async def delete_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> bool | None:
        """
        функция для удаления задачи по id
        """
        task = await self.get_task_for_action(task_id, user_id)
        if not task:
            return None
        stmt = delete(Task).where(Task.task_id == task_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        if result.rowcount > 0:
            return True
        return False
