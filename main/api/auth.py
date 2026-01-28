"""
Маршруты аутентификации: регистрация, вход, выход, обновление токена, получение информации о пользователе.

Этот роутер предоставляет API-эндпоинты для:
- Регистрации нового пользователя
- Авторизации (логин)
- Получения новых access-токенов по refresh-токену
- Выхода из аккаунта (аннулирование refresh-токена)
- Получения информации о текущем пользователе

Используется JWT-аутентификация с OAuth2PasswordBearer.
Токены хранятся/валидируются через Redis.
"""

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
from main.services.auth import oauth2_scheme


router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthRegUserServices:
    """
    Зависимость для получения экземпляра сервиса аутентификации.

    Создаёт репозиторий и сервис с текущей асинхронной сессией.

    :param session: Асинхронная сессия SQLAlchemy
    :return: Экземпляр AuthRegUserServices
    """
    repo = AuthRegUserRepository(db=session)
    return AuthRegUserServices(repository=repo)


@router.post(
    "/register",
    summary="Регистрация нового пользователя",
    description="Создаёт нового пользователя после проверки уникальности email. Пароль хэшируется.",
    response_model=RegistrationOut,
    status_code=201,
)
async def registration_users(
    data: RegistrationIn,
    service: AuthRegUserServices = Depends(get_auth_service),
) -> RegistrationOut:
    """
    Эндпоинт регистрации пользователя.

    :param data: Данные для регистрации (email, пароль, имя, фамилия, отчество)
    :param service: Сервис аутентификации (внедряется через Depends)
    :return: Объект с email нового пользователя
    :raises HTTPException(404): Если email уже занят
    """
    email = await service.registration_services(data=data)
    return RegistrationOut(email=email)


@router.post(
    "/update_acces_token",
    summary="Обновление access-токена",
    description="Генерирует новый access-токен на основе действительного refresh-токена.",
    response_model=OutToken,
)
async def get_token(
    data: GetToken,
    service: AuthRegUserServices = Depends(get_auth_service),
) -> OutToken:
    """
    Обновление access-токена с помощью refresh-токена.

    :param data: Схема, содержащая refresh_token
    :param service: Сервис аутентификации
    :return: Новые access и refresh токены
    :raises HTTPException(401): Если refresh-токен недействителен или отозван
    """
    new_access_token = await service.update_token(data=data.model_dump())
    return OutToken(access_token=new_access_token)


@router.post(
    "/login",
    summary="Авторизация пользователя",
    description="Проверяет email и пароль, возвращает JWT-токены при успешной аутентификации.",
    response_model=Token,
)
async def login_user(
    data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthRegUserServices = Depends(get_auth_service),
) -> Token:
    """
    Вход пользователя в систему.

    Использует стандартную OAuth2-форму (username/password).
    Проверяет существование пользователя и корректность пароля.

    :param data: OAuth2-форма с логином (email) и паролем
    :param service: Сервис аутентификации
    :return: JWT-токены (access + refresh)
    :raises HTTPException(401): При неверных учётных данных
    """
    login_data = LogIn(email=data.username, password=data.password)
    return await service.login_service(login_data)


@router.post(
    "/logout",
    summary="Выход из аккаунта",
    description="Аннулирует refresh-токен, чтобы предотвратить его дальнейшее использование.",
)
async def logout_user(
    data: LogoutRequest,
    service: AuthRegUserServices = Depends(get_auth_service),
):
    """
    Выход пользователя: удаляет refresh-токен из Redis.

    :param data: Запрос, содержащий refresh_token
    :param service: Сервис аутентификации
    :return: Сообщение об успешном выходе
    :raises HTTPException(400): Если токен отсутствует или уже отозван
    """
    return await service.logout_service(data.refresh_token)


@router.get(
    "/info",
    summary="Получение информации о пользователе",
    description="Возвращает основные данные авторизованного пользователя (email, ФИО).",
)
async def get_user_info(
    token: str = Depends(oauth2_scheme),
    service: AuthRegUserServices = Depends(get_auth_service),
):
    """
    Получение информации о текущем пользователе.

    Требуется валидный access-токен (автоматически извлекается из заголовка Authorization).

    :param token: access-токен
    :param service: Сервис аутентификации
    :return: Словарь с полями: email, first_name, last_name, patronymic_name 
    :raises HTTPException(401): Если токен недействителен или истёк
    """
    result = await service.get_current_user(token=token)
    return await service.info_user(user_id=result.user_id)