from dataclasses import dataclass
from uuid import UUID
import uuid
from fastapi import HTTPException
from main.repositories.tasks import TaskRepository
from main.schemas.tasks import TaskCreate, TaskUpdate


@dataclass
class TaskServices:
    repository: TaskRepository

    async def create_task(self, data: TaskCreate) -> UUID:
        return await self.repository.create_task(data)

    async def update_task(self, task_id: UUID, user_id: uuid.UUID, data: TaskUpdate) -> UUID:
        result = await self.repository.update_task(task_id, user_id, data)
        if result is None:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        return result

    async def delete_task(self, task_id: UUID, user_id:uuid.UUID) -> bool:
        result = await self.repository.delete_task(task_id, user_id)
        if result is None:
            raise HTTPException(
                status_code=404, 
                detail="Задача не найдена или у вас нет прав"
            )
        return result
