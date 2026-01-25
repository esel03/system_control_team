from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence
from uuid import UUID
import uuid
from fastapi import HTTPException
from main.db.models.tasks import Task
from main.repositories.tasks import TaskRepository
from main.schemas.tasks import ListTasksUserOut, TaskCreate, TaskUpdate, ListTasksOut
from main.repositories.team_management import RoomTeamRepository

@dataclass
class TaskServices:
    repository: TaskRepository
    room_team_repo : RoomTeamRepository
    
    async def create_task(self, data: TaskCreate, author_id: uuid.UUID) -> UUID:
        return await self.repository.create_task(data, author_id)

    async def update_task(
        self, task_id: UUID, user_id: uuid.UUID, data: TaskUpdate
    ) -> UUID:
        result = await self.repository.update_task(task_id, user_id, data)
        if result is None:
            raise HTTPException(
                status_code=404, detail="Задача не найдена или у вас нет прав"
            )
        return result

    async def delete_task(self, task_id: UUID, user_id: uuid.UUID) -> bool:
        result = await self.repository.delete_task(task_id, user_id)
        if result is None:
            raise HTTPException(
                status_code=404, detail="Задача не найдена или у вас нет прав"
            )
        return result

    async def get_tasks_for_team(
        self, team_id: UUID, days_arg: int
    ) -> list[ListTasksOut]:
        if days_arg < 1:
            raise HTTPException(
                status_code=400, detail="Количество дней должно быть больше 0"
            )
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_arg)
        tasks = await self.repository.get_tasks_for_team(team_id, start_date, end_date)
        return [ListTasksOut.model_validate(task) for task in tasks]
            

    async def get_tasks_for_user_in_team(
        self, user_id: uuid.UUID, team_id: UUID, days_arg: int
    ) -> list[ListTasksUserOut]:
        if days_arg < 1:
            raise HTTPException(
                status_code=400, detail="Количество дней должно быть больше 0"
            )
        if not await self.room_team_repo.check_user_in_team(user_id, team_id):
            raise HTTPException(
                status_code=404, detail="Пользователь не найден в команде"
            )
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_arg)
        tasks = await self.repository.get_tasks_for_user_in_team(
            user_id, team_id, start_date, end_date
        )
        return [ListTasksUserOut.model_validate(task) for task in tasks]
            
