from fastapi import APIRouter, Depends
from main.db.connect import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from main.services.auth import AuthRegUserServices
from main.repositories.auth import AuthRegUserRepository
from main.schemas.auth import RegistrationIn, RegistrationOut

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthRegUserServices:
    repo = AuthRegUserRepository(db=session)
    return AuthRegUserServices(repository=repo)


@router.post("/", summary="Регистрация пользователя", response_model=RegistrationOut)
async def registration_users(
    data: RegistrationIn, service: AuthRegUserServices = Depends(get_auth_service)
):
    return {'token': f'{await service.registration_services(data=data)}'}
