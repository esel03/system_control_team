from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from main.db.connect import get_async_session
from main.repositories.auth import AuthRegUserRepository
from main.schemas.auth import (
    GetToken,
    LogIn,
    LogoutRequest,
    MessageOut,
    RegistrationIn,
    RegistrationOut,
    Token,
    TokenData,
    UserProfileOut,
)
from main.services.auth import AuthRegUserServices, oauth2_scheme
from main.services.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthRegUserServices:
    return AuthRegUserServices(repository=AuthRegUserRepository(db=session))


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: AuthRegUserServices = Depends(get_auth_service),
) -> TokenData:
    return await service.get_current_user(token)


def _client_identity(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()
    return request.client.host if request.client else "unknown"


@router.post(
    "/register",
    summary="Регистрация пользователя",
    response_model=RegistrationOut,
    status_code=status.HTTP_201_CREATED,
)
async def registration_users(
    data: RegistrationIn,
    request: Request,
    service: AuthRegUserServices = Depends(get_auth_service),
) -> RegistrationOut:
    await enforce_rate_limit(_client_identity(request), "register", 5, 3600)
    email = await service.registration_services(data=data)
    return RegistrationOut(email=email)


@router.post(
    "/refresh",
    summary="Обновление пары токенов",
    response_model=Token,
)
async def refresh_token(
    data: GetToken,
    request: Request,
    service: AuthRegUserServices = Depends(get_auth_service),
) -> Token:
    await enforce_rate_limit(_client_identity(request), "refresh", 20, 60)
    return await service.update_token(data.refresh_token)


@router.post("/login", summary="Авторизация пользователя", response_model=Token)
async def login_user(
    data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    service: AuthRegUserServices = Depends(get_auth_service),
) -> Token:
    await enforce_rate_limit(_client_identity(request), "login", 10, 60)
    return await service.login_service(
        LogIn(email=data.username, password=data.password)
    )


@router.post("/logout", summary="Выход пользователя", response_model=MessageOut)
async def logout_user(
    data: LogoutRequest,
    current_user: TokenData = Depends(get_current_user),
    service: AuthRegUserServices = Depends(get_auth_service),
) -> dict[str, str]:
    return await service.logout_service(data.refresh_token, current_user.user_id)


@router.get("/me", summary="Текущий пользователь", response_model=UserProfileOut)
async def get_user_profile(
    current_user: TokenData = Depends(get_current_user),
    service: AuthRegUserServices = Depends(get_auth_service),
) -> UserProfileOut:
    return await service.get_user_profile(current_user.user_id)
