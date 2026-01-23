from dataclasses import dataclass
from uuid import UUID
from fastapi import HTTPException
from main.repositories.tasks import TaskRepository
from main.schemas.tasks import TaskCreate, TaskUpdate


@dataclass
class TaskService:
    repository: TaskRepository

    async def create_task(self, data: TaskCreate) -> UUID:
        return await self.repository.create_task(data)

    async def update_task(self, task_id: UUID, data: TaskUpdate) -> UUID | None:
        result = await self.repository.update_task(task_id, data)
        if result is None:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        return result

    async def delete_task(self, task_id: UUID) -> bool:
        result = await self.repository.delete_task(task_id)
        return result
