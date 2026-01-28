from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import HTTPException
from main.repositories.tasks import TaskRepository
from main.schemas.tasks import (
    TaskCreate,
    TaskUpdate,
    ListTasksOut,
    TaskUserStatsOut,
    TaskTeamStatsOut,
)



@dataclass
class TaskServices:
    repository: TaskRepository

    async def create_task(self, data: TaskCreate, author_id: UUID) -> UUID:
        if not await self.repository.check_user_exists(author_id):
            raise HTTPException(
                status_code=404, detail="Такого пользователя не существует"
            )
        if not await self.repository.check_user_is_chief(author_id, data.team_id):
            raise HTTPException(
                status_code=403, detail="Пользователь не является руководителем"
            )
        if not await self.repository.check_user_in_team(author_id, data.team_id):
            raise HTTPException(
                status_code=404, detail="Пользователь не найден в комнате"
            )
        if data.executor and not await self.repository.check_user_in_team(
            data.executor, data.team_id
        ):
            raise HTTPException(
                status_code=400, detail="Исполнитель не состоит в команде"
            )
        if data.task_deadline_date is not None:
            if data.task_deadline_date <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=400,
                    detail="Дата дедлайна не может быть меньше либо равна текущей даты",
                )
        return await self.repository.create_task(data, author_id)

    async def update_task(
        self, data: TaskUpdate, task_id: UUID, author_id: UUID
    ) -> UUID:
        if not await self.repository.check_user_exists(author_id):
            raise HTTPException(
                status_code=404, detail="Такого пользователя не существует"
            )
        task = await self.repository.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        if not await self.repository.check_user_in_team(author_id, task.team_id):
            raise HTTPException(
                status_code=404, detail="Пользователь не найден в комнате"
            )
        if not (
            await self.repository.check_user_is_chief(author_id, task.team_id)
            or await self.repository.check_user_is_task_creator(author_id, task_id)
        ):
            raise HTTPException(
                status_code=404,
                detail="Пользователь не является руководителем или автором задачи",
            )
        if data.task_deadline_date is not None:
            if data.task_deadline_date <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=400,
                    detail="Дата дедлайна не может быть меньше либо равна текущей даты",
                )
        return await self.repository.update_task(data, task_id, author_id)

    async def delete_task(self, task_id: UUID, author_id: UUID) -> bool:
        if not await self.repository.check_user_exists(author_id):
            raise HTTPException(
                status_code=404, detail="Такого пользователя не существует"
            )
        task = await self.repository.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        if not (
            await self.repository.check_user_is_chief(author_id, task.team_id)
            or await self.repository.check_user_is_task_creator(author_id, task_id)
        ):
            raise HTTPException(
                status_code=404,
                detail="Пользователь не является руководителем или автором задачи",
            )
        return await self.repository.delete_task(task_id)

    async def complete_task(self, task_id: UUID, user_id: UUID):
        if not await self.repository.check_user_exists(user_id):
            raise HTTPException(
                status_code=404, detail="Такого пользователя не существует"
            )
        task = await self.repository.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        return await self.repository.complete_task(task_id, user_id)

    async def get_team_tasks(
        self, team_id: UUID, inspector_id: UUID, completed: bool, days: int
    ) -> list[ListTasksOut]:
        if not await self.repository.check_team_exists(team_id):
            raise HTTPException(status_code=404, detail="Такой командs не существует")
        if not await self.repository.check_user_is_chief(inspector_id, team_id):
            raise HTTPException(
                status_code=403,
                detail="Только руководитель может просматривать задачи команды",
            )
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        return await self.repository.get_team_tasks(
            team_id, completed, start_date, end_date
        )

    async def get_user_tasks(
        self,
        team_id: UUID,
        user_id: UUID,
        inspector_id: UUID,
        completed: bool,
        days: int,
    ) -> list[ListTasksOut]:
        if not await self.repository.check_team_exists(team_id):
            raise HTTPException(status_code=404, detail="Такой команды не существует")
        if not await self.repository.check_user_exists(user_id):
            raise HTTPException(
                status_code=404, detail="Такого пользователя не существует"
            )
        if not await self.repository.check_user_in_team(user_id, team_id):
            raise HTTPException(403, "Пользователь не состоит в команде")
        if user_id != inspector_id and not await self.repository.check_user_is_chief(
            inspector_id, team_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Недостаточно прав для просмотра задач пользователя",
            )
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        return await self.repository.get_user_tasks(
            team_id, user_id, completed, start_date, end_date
        )

    async def get_user_task_statistics(
        self, team_id: UUID, user_id: UUID, inspector_id: UUID, days: int
    ) -> TaskUserStatsOut:
        if not await self.repository.check_team_exists(team_id):
            raise HTTPException(status_code=404, detail="Команда не найдена")

        if not await self.repository.check_user_exists(user_id):
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        if not await self.repository.check_user_in_team(user_id, team_id):
            raise HTTPException(
                status_code=403, detail="Пользователь не состоит в команде"
            )
        if inspector_id != user_id and not await self.repository.check_user_is_chief(
            inspector_id, team_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Недостаточно прав для просмотра статистики пользователя",
            )
        if days < 1:
            raise HTTPException(
                status_code=400, detail="Количество дней должно быть больше 0"
            )
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        user_completed = await self.repository.count_user_completed_tasks(
            team_id=team_id, user_id=user_id, start_date=start_date, end_date=end_date
        )
        user_in_progress = await self.repository.count_user_in_progress_tasks(
            team_id=team_id, user_id=user_id
        )
        return TaskUserStatsOut(
            completed=user_completed,
            in_progress=user_in_progress,
        )

    async def get_team_task_statistics(
        self, team_id: UUID, inspector_id: UUID, days: int = 0
    ) -> TaskTeamStatsOut:
        if not await self.repository.check_team_exists(team_id):
            raise HTTPException(404, "Команда не найдена")
        if not await self.repository.check_user_is_chief(inspector_id, team_id):
            raise HTTPException(
                403, "Только шеф команды может просматривать статистику команды"
            )
        if days < 1:
            raise HTTPException(
                status_code=400, detail="Количество дней должно быть больше 0"
            )
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        team_completed = await self.repository.count_team_completed_tasks(
            team_id, start_date, end_date
        )
        team_in_progress = await self.repository.count_team_in_progress_tasks(team_id)
        return TaskTeamStatsOut(completed=team_completed, in_progress=team_in_progress)
