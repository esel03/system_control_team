from typing import Annotated
from fastapi import APIRouter, Depends
from main.db.connect import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from main.services.auth import AuthRegUserServices
from main.repositories.auth import AuthRegUserRepository
from main.schemas.auth import (
    LogoutRequest,
    RegistrationIn,
    RegistrationOut,
    GetToken,
    OutToken,
)
from main.schemas.auth import LogIn, Token
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthRegUserServices:
    repo = AuthRegUserRepository(db=session)
    return AuthRegUserServices(repository=repo)


@router.post(
    "/register", summary="Регистрация пользователя", response_model=RegistrationOut
)
async def registration_users(
    data: RegistrationIn, service: AuthRegUserServices = Depends(get_auth_service)
) -> dict[str, str]:
    return RegistrationOut(email=await service.registration_services(data=data))


@router.post("/update_acces_token", summary="Получение токена", response_model=OutToken)
async def get_token(
    data: GetToken, service: AuthRegUserServices = Depends(get_auth_service)
) -> OutToken:
    return OutToken(access_token=await service.update_token(data=data.model_dump()))


@router.post("/login", summary="авторизация пользователя", response_model=Token)
async def login_user(
    data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthRegUserServices = Depends(get_auth_service),
) -> Token:
    login_data = LogIn(email=data.username, password=data.password)
    return await service.login_service(login_data)


@router.post("/logout", summary="выход пользователя")
async def logout_user(
    data: LogoutRequest,
    service: AuthRegUserServices = Depends(get_auth_service),
):
    return await service.logout_service(data.refresh_token)
