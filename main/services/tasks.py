import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException

from main.db.models.tasks import Status, Task
from main.repositories.tasks import TaskRepository
from main.schemas.tasks import (
    TaskCreate,
    TaskListOut,
    TaskTeamStatsOut,
    TaskUpdate,
    TaskUserStatsOut,
)

logger = logging.getLogger(__name__)


@dataclass
class TaskServices:
    repository: TaskRepository

    async def create_task(
        self,
        data: TaskCreate,
        team_id: UUID,
        author_id: UUID,
    ) -> UUID:
        if not await self.repository.check_team_exists(team_id):
            raise HTTPException(status_code=404, detail="Команда не найдена")
        if not await self.repository.check_user_is_chief(author_id, team_id):
            raise HTTPException(
                status_code=403,
                detail="Требуются права руководителя команды",
            )
        if data.executor and not await self.repository.check_user_in_team(
            data.executor,
            team_id,
        ):
            raise HTTPException(
                status_code=400,
                detail="Исполнитель не состоит в команде",
            )
        self._validate_deadline(data.task_deadline_date)
        task_status = Status.assigned if data.executor else Status.unassigned
        task_id = await self.repository.create_task(
            data,
            team_id,
            author_id,
            task_status,
            datetime.now(UTC),
        )
        logger.info(
            "task_created actor=%s task=%s team=%s", author_id, task_id, team_id
        )
        return task_id

    async def update_task(
        self,
        data: TaskUpdate,
        task_id: UUID,
        actor_id: UUID,
    ) -> UUID:
        task = await self._get_task(task_id)
        await self._require_task_editor(task, actor_id)
        if task.status in (Status.completed, Status.canceled):
            raise HTTPException(
                status_code=409,
                detail="Завершённую или отменённую задачу нельзя редактировать",
            )

        updates = data.model_dump(exclude_unset=True)
        if "task_deadline_date" in updates:
            self._validate_deadline(updates["task_deadline_date"])

        executor = updates.get("executor", task.executor)
        if "executor" in updates and executor is not None:
            if not await self.repository.check_user_in_team(executor, task.team_id):
                raise HTTPException(
                    status_code=400,
                    detail="Исполнитель не состоит в команде",
                )

        requested_status = updates.get("status")
        if requested_status in (Status.assigned, Status.in_progress) and not executor:
            raise HTTPException(
                status_code=400,
                detail="Для этого статуса требуется исполнитель",
            )
        if requested_status == Status.unassigned and executor:
            raise HTTPException(
                status_code=400,
                detail="Статус unassigned несовместим с исполнителем",
            )

        if "executor" in updates and "status" not in updates:
            updates["status"] = Status.assigned if executor else Status.unassigned
        if requested_status == Status.canceled:
            updates["task_finish_date"] = datetime.now(UTC)

        if not updates:
            return task_id
        updated_id = await self.repository.update_task(
            task,
            updates,
            actor_id,
            datetime.now(UTC),
        )
        logger.info("task_updated actor=%s task=%s", actor_id, task_id)
        return updated_id

    async def delete_task(self, task_id: UUID, actor_id: UUID) -> None:
        task = await self._get_task(task_id)
        await self._require_task_editor(task, actor_id)
        deleted = await self.repository.soft_delete_task(
            task_id,
            actor_id,
            datetime.now(UTC),
        )
        if not deleted:
            raise HTTPException(status_code=409, detail="Задача уже удалена")
        logger.info("task_deleted actor=%s task=%s", actor_id, task_id)

    async def complete_task(self, task_id: UUID, actor_id: UUID) -> None:
        task = await self._get_task(task_id)
        await self._require_team_member(actor_id, task.team_id)
        is_chief = await self.repository.check_user_is_chief(
            actor_id,
            task.team_id,
        )
        if task.executor != actor_id and not is_chief:
            raise HTTPException(
                status_code=403,
                detail="Завершить задачу может исполнитель или руководитель",
            )
        if task.executor is None:
            raise HTTPException(
                status_code=409,
                detail="Нельзя завершить задачу без исполнителя",
            )
        if task.status in (Status.completed, Status.canceled):
            raise HTTPException(status_code=409, detail="Задача уже закрыта")
        if not await self.repository.complete_task(
            task_id,
            actor_id,
            datetime.now(UTC),
        ):
            raise HTTPException(status_code=409, detail="Состояние задачи изменилось")
        logger.info("task_completed actor=%s task=%s", actor_id, task_id)

    async def get_team_tasks(
        self,
        team_id: UUID,
        inspector_id: UUID,
        task_status: Status | None,
        days: int,
        limit: int,
        offset: int,
    ) -> TaskListOut:
        await self._require_team_member(inspector_id, team_id)
        start_date, end_date = self._period(days)
        items, total = await self.repository.get_team_tasks(
            team_id,
            task_status,
            start_date,
            end_date,
            limit,
            offset,
        )
        return TaskListOut(items=items, total=total, limit=limit, offset=offset)

    async def get_user_tasks(
        self,
        team_id: UUID,
        user_id: UUID,
        inspector_id: UUID,
        task_status: Status | None,
        days: int,
        limit: int,
        offset: int,
    ) -> TaskListOut:
        await self._require_team_member(user_id, team_id)
        if user_id != inspector_id and not await self.repository.check_user_is_chief(
            inspector_id,
            team_id,
        ):
            raise HTTPException(
                status_code=403,
                detail="Недостаточно прав для просмотра задач пользователя",
            )
        start_date, end_date = self._period(days)
        items, total = await self.repository.get_user_tasks(
            team_id,
            user_id,
            task_status,
            start_date,
            end_date,
            limit,
            offset,
        )
        return TaskListOut(items=items, total=total, limit=limit, offset=offset)

    async def get_user_task_statistics(
        self,
        team_id: UUID,
        user_id: UUID,
        inspector_id: UUID,
        days: int,
    ) -> TaskUserStatsOut:
        await self._require_team_member(user_id, team_id)
        if inspector_id != user_id and not await self.repository.check_user_is_chief(
            inspector_id,
            team_id,
        ):
            raise HTTPException(
                status_code=403,
                detail="Недостаточно прав для просмотра статистики пользователя",
            )
        start_date, end_date = self._period(days)
        return TaskUserStatsOut(
            completed=await self.repository.count_user_completed_tasks(
                team_id,
                user_id,
                start_date,
                end_date,
            ),
            in_progress=await self.repository.count_user_in_progress_tasks(
                team_id,
                user_id,
            ),
        )

    async def get_team_task_statistics(
        self,
        team_id: UUID,
        inspector_id: UUID,
        days: int,
    ) -> TaskTeamStatsOut:
        await self._require_team_member(inspector_id, team_id)
        start_date, end_date = self._period(days)
        return TaskTeamStatsOut(
            completed=await self.repository.count_team_completed_tasks(
                team_id,
                start_date,
                end_date,
            ),
            in_progress=await self.repository.count_team_in_progress_tasks(team_id),
        )

    async def _get_task(self, task_id: UUID) -> Task:
        task = await self.repository.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        return task

    async def _require_task_editor(self, task: Task, actor_id: UUID) -> None:
        if not await self.repository.check_user_in_team(actor_id, task.team_id):
            raise HTTPException(status_code=403, detail="Нет доступа к команде")
        if task.author != actor_id and not await self.repository.check_user_is_chief(
            actor_id,
            task.team_id,
        ):
            raise HTTPException(
                status_code=403,
                detail="Редактировать задачу может автор или руководитель",
            )

    async def _require_team_member(self, user_id: UUID, team_id: UUID) -> None:
        if not await self.repository.check_team_exists(team_id):
            raise HTTPException(status_code=404, detail="Команда не найдена")
        if not await self.repository.check_user_in_team(user_id, team_id):
            raise HTTPException(status_code=403, detail="Нет доступа к команде")

    @staticmethod
    def _period(days: int) -> tuple[datetime, datetime]:
        if not 1 <= days <= 3650:
            raise HTTPException(
                status_code=400,
                detail="Количество дней должно быть от 1 до 3650",
            )
        end_date = datetime.now(UTC)
        return end_date - timedelta(days=days), end_date

    @staticmethod
    def _validate_deadline(deadline: datetime | None) -> None:
        if deadline is not None and deadline <= datetime.now(UTC):
            raise HTTPException(
                status_code=400,
                detail="Дедлайн должен быть позже текущего времени",
            )
