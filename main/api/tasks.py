from uuid import UUID
from fastapi import APIRouter, Depends
from main.db.connect import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from main.api.auth import get_auth_service
from main.services.tasks import TaskServices
from main.services.auth import AuthRegUserServices
from main.repositories.tasks import TaskRepository
from main.schemas.tasks import (
    ListTasksOut,
    TaskCreate,
    TaskOut,
    TaskUpdate,
    TaskUserStatsOut,
    TaskTeamStatsOut,
)
from main.services.auth import oauth2_scheme

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(
    session: AsyncSession = Depends(get_async_session),
) -> TaskServices:
    repo = TaskRepository(db=session)
    return TaskServices(repository=repo)


@router.post("/create", summary="Создание задачи", response_model=TaskOut)
async def create_task(
    data: TaskCreate,
    token: str = Depends(oauth2_scheme),
    service: TaskServices = Depends(get_task_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> TaskOut:
    """
    Создаёт новую задачу.

    Параметры:
    - data: данные для создания задачи (заголовок, описание, исполнитель, сроки).
    - token: токен аутентификации текущего пользователя.

    Доступ:
    - авторизованный пользователь может создать задачу.

    Возвращает:
    - идентификатор созданной задачи.
    """
    token_data = await service_auth.get_current_user(token=token)

    task_id = await service.create_task(
        data=data,
        author_id=token_data.user_id,
    )
    return TaskOut(task_id=task_id)


@router.post("/update/{task_id}", summary="Обновление задачи", response_model=TaskOut)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    token: str = Depends(oauth2_scheme),
    service: TaskServices = Depends(get_task_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> TaskOut:
    """
    Обновляет существующую задачу.

    Параметры:
    - task_id: идентификатор задачи для обновления.
    - data: новые данные задачи.
    - token: токен аутентификации текущего пользователя.

    Доступ:
    - автор задачи может редактировать её.

    Возвращает:
    - идентификатор обновлённой задачи.
    """
    token_data = await service_auth.get_current_user(token=token)

    update_task_id = await service.update_task(
        data=data,
        task_id=task_id,
        author_id=token_data.user_id,
    )
    return TaskOut(task_id=update_task_id)


@router.delete("/delete/{task_id}", summary="Удаление задачи", status_code=204)
async def delete_task(
    task_id: UUID,
    token: str = Depends(oauth2_scheme),
    service: TaskServices = Depends(get_task_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> None:
    """
    Удаляет задачу по идентификатору.

    Параметры:
    - task_id: идентификатор задачи для удаления.
    - token: токен аутентификации текущего пользователя.

    Доступ:
    - только автор задачи может её удалить.

    Возвращает:
    - статус 204 (No Content) при успешном удалении.
    """
    token_data = await service_auth.get_current_user(token=token)

    await service.delete_task(
        task_id=task_id,
        author_id=token_data.user_id,
    )
    return None


@router.get("/teams/{team_id}/tasks", summary="Получить задачи команды")
async def get_team_tasks(
    team_id: UUID,
    completed: bool,
    days: int = 7,
    token: str = Depends(oauth2_scheme),
    service: TaskServices = Depends(get_task_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> list[ListTasksOut]:
    """
    Получает список задач команды за указанный период.

    Параметры:
    - team_id: идентификатор команды.
    - completed: флаг завершённых задач (True/False).
    - days: количество дней для фильтрации (по умолчанию 7).
    - token: токен аутентификации текущего пользователя.

    Доступ:
    - члены команды,
    - руководитель команды.

    Возвращает:
    - список задач команды с основной информацией.
    """
    token_data = await service_auth.get_current_user(token)
    return await service.get_team_tasks(team_id, token_data.user_id, completed, days)


@router.get("/teams/{team_id}/users/{user_id}/tasks", summary="Получить задачи команды")
async def get__user_in_team_tasks(
    team_id: UUID,
    user_id: UUID,
    completed: bool,
    days: int = 7,
    token: str = Depends(oauth2_scheme),
    service: TaskServices = Depends(get_task_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> list[ListTasksOut]:
    """
    Получает список задач конкретного пользователя в команде.

    Параметры:
    - team_id: идентификатор команды.
    - user_id: идентификатор пользователя.
    - completed: флаг завершённых задач (True/False).
    - days: количество дней для фильтрации (по умолчанию 7).
    - token: токен аутентификации текущего пользователя.

    Доступ:
    - сам пользователь,
    - руководитель команды.

    Возвращает:
    - список задач указанного пользователя.
    """
    inspector = await service_auth.get_current_user(token)
    return await service.get_user_tasks(
        team_id, user_id, inspector.user_id, completed, days
    )


@router.get(
    "/stats/user/{user_id}",
    response_model=TaskUserStatsOut,
    summary="Получить статистику задач пользователя",
)
async def get_user_task_stats(
    user_id: UUID,
    team_id: UUID,
    days: int = 7,
    token: str = Depends(oauth2_scheme),
    service: TaskServices = Depends(get_task_service),
    service_auth: AuthRegUserServices = Depends(get_auth_service),
) -> TaskUserStatsOut:
    """
    Получает статистику задач пользователя:
    - количество завершённых за последние N дней,
    - количество незавершённых.

    Доступ:
    - сам пользователь,
    - руководитель команды.
    """
    token_data = await service_auth.get_current_user(token)
    inspector = token_data.user_id
    stats = await service.get_user_task_statistics(
        team_id=team_id, user_id=user_id, inspector_id=inspector, days=days
    )
    return stats


@router.get(
    "/stats/user/{user_id}",
    response_model=TaskTeamStatsOut,
    summary="Получить статистику задач пользователя",
)
async def get_team_task_stats(
    team_id: UUID,
    days: int = 7,
    token: str = Depends(oauth2_scheme),
    service: TaskServices = Depends(get_task_service),
    auth: AuthRegUserServices = Depends(get_auth_service),
) -> TaskTeamStatsOut:
    """
    Получает статистику задач команды:
    - количество завершённых задач за последние N дней,
    - количество незавершённых задач.

    Параметры:
    - team_id: идентификатор команды.
    - days: количество дней для анализа.
    - token: токен аутентификации текущего пользователя.

    Доступ:
    - члены команды,
    - руководитель команды.

    Возвращает:
    - объект с количеством завершённых и незавершённых задач.
    """
    inspector = await auth.get_current_user(token)
    return await service.get_team_task_statistics(
        team_id=team_id, inspector_id=inspector.user_id, days=days
    )
