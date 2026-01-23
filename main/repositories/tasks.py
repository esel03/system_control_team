from dataclasses import dataclass
import uuid
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from main.db.models.tasks import Task
from main.schemas.tasks import TaskCreate, TaskUpdate


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
        stmt = Task(**data.model_dump())
        self.db.add(stmt)
        await self.db.commit()
        await self.db.refresh(stmt)
        return stmt.task_id

    async def update_task(self, task_id: uuid.UUID, data: TaskUpdate) -> uuid.UUID:
        """
        функция для обновления задачи по id и возвращает id обновленной задачи
        """
        updated_data = data.model_dump(exclude_unset=True)
        if not updated_data:
            return task_id
        stmt = (
            update(Task)
            .where(Task.task_id == task_id)
            .values(**updated_data)
            .execution_options(synchronize_session=False)
        )
        await self.db.execute(stmt)
        await self.db.commit()
        return task_id
    
    from sqlalchemy import delete

async def delete_task(self, task_id: uuid.UUID) -> bool:
    """
    функция для удаления задачи по id
    """
    stmt = (
        delete(Task)
        .where(Task.task_id == task_id)
        .execution_options(synchronize_session=False)
    )
    result = await self.db.execute(stmt)
    await self.db.commit()
    if result.rowcount > 0:
        return True
    return False

