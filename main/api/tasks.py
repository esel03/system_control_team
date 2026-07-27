from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from main.api.auth import get_current_user
from main.db.connect import get_async_session
from main.db.models.tasks import Status
from main.repositories.tasks import TaskRepository
from main.schemas.auth import TokenData
from main.schemas.tasks import (
    TaskCreate,
    TaskListOut,
    TaskOut,
    TaskTeamStatsOut,
    TaskUpdate,
    TaskUserStatsOut,
)
from main.services.tasks import TaskServices

router = APIRouter(tags=["tasks"])


def get_task_service(
    session: AsyncSession = Depends(get_async_session),
) -> TaskServices:
    return TaskServices(repository=TaskRepository(db=session))


PageLimit = Annotated[int, Query(ge=1, le=100)]
PageOffset = Annotated[int, Query(ge=0)]
PeriodDays = Annotated[int, Query(ge=1, le=3650)]


@router.post(
    "/teams/{team_id}/tasks",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    team_id: UUID,
    data: TaskCreate,
    current_user: TokenData = Depends(get_current_user),
    service: TaskServices = Depends(get_task_service),
) -> TaskOut:
    task_id = await service.create_task(data, team_id, current_user.user_id)
    return TaskOut(task_id=task_id)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    current_user: TokenData = Depends(get_current_user),
    service: TaskServices = Depends(get_task_service),
) -> TaskOut:
    updated_id = await service.update_task(data, task_id, current_user.user_id)
    return TaskOut(task_id=updated_id)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    service: TaskServices = Depends(get_task_service),
) -> Response:
    await service.delete_task(task_id, current_user.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/tasks/{task_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_task(
    task_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    service: TaskServices = Depends(get_task_service),
) -> Response:
    await service.complete_task(task_id, current_user.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/teams/{team_id}/tasks", response_model=TaskListOut)
async def get_team_tasks(
    team_id: UUID,
    task_status: Status | None = None,
    days: PeriodDays = 7,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
    current_user: TokenData = Depends(get_current_user),
    service: TaskServices = Depends(get_task_service),
) -> TaskListOut:
    return await service.get_team_tasks(
        team_id,
        current_user.user_id,
        task_status,
        days,
        limit,
        offset,
    )


@router.get(
    "/teams/{team_id}/users/{user_id}/tasks",
    response_model=TaskListOut,
)
async def get_user_tasks(
    team_id: UUID,
    user_id: UUID,
    task_status: Status | None = None,
    days: PeriodDays = 7,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
    current_user: TokenData = Depends(get_current_user),
    service: TaskServices = Depends(get_task_service),
) -> TaskListOut:
    return await service.get_user_tasks(
        team_id,
        user_id,
        current_user.user_id,
        task_status,
        days,
        limit,
        offset,
    )


@router.get(
    "/teams/{team_id}/users/{user_id}/stats",
    response_model=TaskUserStatsOut,
)
async def get_user_task_stats(
    team_id: UUID,
    user_id: UUID,
    days: PeriodDays = 7,
    current_user: TokenData = Depends(get_current_user),
    service: TaskServices = Depends(get_task_service),
) -> TaskUserStatsOut:
    return await service.get_user_task_statistics(
        team_id,
        user_id,
        current_user.user_id,
        days,
    )


@router.get("/teams/{team_id}/stats", response_model=TaskTeamStatsOut)
async def get_team_task_stats(
    team_id: UUID,
    days: PeriodDays = 7,
    current_user: TokenData = Depends(get_current_user),
    service: TaskServices = Depends(get_task_service),
) -> TaskTeamStatsOut:
    return await service.get_team_task_statistics(
        team_id,
        current_user.user_id,
        days,
    )
