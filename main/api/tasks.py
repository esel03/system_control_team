import uuid
from fastapi import APIRouter, Depends
from main.db.connect import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from main.api.auth import get_auth_service
from main.services.tasks import TaskServices
from main.services.auth import AuthRegUserServices
from main.repositories.tasks import TaskRepository
from main.schemas.tasks import TaskCreate, TaskOut, TaskUpdate
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
    update_task_id = await service.update_task(task_id=task_id, user_id = token_data.user_id, data=data)
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
    
