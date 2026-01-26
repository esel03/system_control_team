import uuid
from fastapi import APIRouter, Depends
from main.db.connect import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from main.api.auth import get_auth_service
from main.services.tasks import TaskServices
from main.services.auth import AuthRegUserServices
from main.repositories.tasks import TaskRepository
from main.repositories.team_management import RoomTeamRepository
from main.schemas.tasks import (
    TaskCreate,
    TaskOut,
    TaskUpdate,
    ListTasksOut,
    ListTasksUserOut,
)
from main.services.auth import oauth2_scheme

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(
    session: AsyncSession = Depends(get_async_session),
) -> TaskServices:
    repo = TaskRepository(db=session)
    room_team_repo = RoomTeamRepository(db=session)
    return TaskServices(repository=repo, room_team_repo=room_team_repo)


@router.post("/create", summary="Создание задачи", response_model=TaskOut)
async def create_task(
    data: TaskCreate,
    token: str = Depends(oauth2_scheme),
    service: TaskServices = Depends(get_task_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> TaskOut:
    token_data = await service_auth.get_current_user(token=token)
    task_id = await service.create_task(data, author_id=token_data.user_id)
    return TaskOut(task_id=task_id)


@router.post("/update/{task_id}", summary="Обновление задачи", response_model=TaskOut)
async def update_task(
    data: TaskUpdate,
    task_id: uuid.UUID,
    token: str = Depends(oauth2_scheme),
    service: TaskServices = Depends(get_task_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> TaskOut:
    token_data = await service_auth.get_current_user(token=token)
    update_task_id = await service.update_task(
        task_id=task_id, user_id=token_data.user_id, data=data
    )
    return TaskOut(task_id=update_task_id)


@router.delete("/delete/{task_id}", summary="Удаление задачи", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    token: str = Depends(oauth2_scheme),
    service: TaskServices = Depends(get_task_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> None:
    token_data = await service_auth.get_current_user(token=token)
    await service.delete_task(task_id=task_id, user_id=token_data.user_id)
    return None


@router.get(
    "/statistics/{team_id}/{user_id}",
    summary="Статистика пользователя из команды по задачам за n-дней",
    response_model=list[ListTasksUserOut],
)
async def get_period_tasks_for_user_in_team(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    days: int,
    token: str = Depends(oauth2_scheme),
    service: TaskServices = Depends(get_task_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> list[ListTasksUserOut]:
    token_data = await service_auth.get_current_user(token=token)
    return await service.get_tasks_for_user_in_team(user_id, team_id, days)


@router.get(
    "/statistics/{team_id}",
    summary="Статистика команды по задачам за n-дней",
    response_model=list[ListTasksOut],
)
async def get_period_tasks_for_team(
    team_id: uuid.UUID,
    days: int,
    token: str = Depends(oauth2_scheme),
    service: TaskServices = Depends(get_task_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> list[ListTasksOut]:
    token_data = await service_auth.get_current_user(token=token)
    return await service.get_tasks_for_team(team_id, days)
