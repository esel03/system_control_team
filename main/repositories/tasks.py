from dataclasses import dataclass
import uuid
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from main.db.models.tasks import Task
from main.schemas.tasks import TaskCreate, TaskUpdate
from datetime import datetime, timezone


@dataclass
class TaskRepository:
    db: AsyncSession

    async def get_task(self, task_id: uuid.UUID) -> Task | None:
        """
        функция для получения задачи по id
        """
        stmt = select(Task).where(Task.task_id == task_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_task(self, data: TaskCreate) -> uuid.UUID:
        """
        функция для создания задачи, возвращает id созданной задачи
        """
        stmt = Task(
            **data.model_dump(),
            task_create_date=datetime.now(timezone.utc),
            task_update_date=None
        )
        self.db.add(stmt)
        await self.db.commit()
        await self.db.refresh(stmt)
        return stmt.task_id

    async def update_task(
        self, task_id: uuid.UUID, data: TaskUpdate
    ) -> uuid.UUID | None:
        """
        функция обновления задачи по ID.
        """
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            update_data = {}
        update_data["task_update_date"] = datetime.now(timezone.utc)
        stmt = update(Task).where(Task.task_id == task_id).values(**update_data)
        result = await self.db.execute(stmt)
        if result.rowcount == 0:
            return None
        await self.db.commit()
        return task_id

    async def delete_task(self, task_id: uuid.UUID) -> bool:
        """
        функция для удаления задачи по id
        """
        stmt = delete(Task).where(Task.task_id == task_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        if result.rowcount > 0:
            return True
        return False
