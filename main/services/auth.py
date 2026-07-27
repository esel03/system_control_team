from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError

from main.repositories.auth import AuthRegUserRepository
from main.schemas.auth import LogIn, RegistrationIn, Token, TokenData, UserProfileOut
from main.services.jwt import JwtAuth
from main.services.utils import Utils

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
jwt_token = JwtAuth()
utils = Utils()


@dataclass
class AuthRegUserServices:
    repository: AuthRegUserRepository

    async def registration_services(self, data: RegistrationIn) -> str:
        if await self.repository.get_email(str(data.email)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email уже существует",
            )
        data.password = await utils.get_password_hash(data.password)
        try:
            return await self.repository.create_user(data)
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email уже существует",
            ) from exc

    async def update_token(self, refresh_token: str) -> Token:
        payload = jwt_token.decode_token(refresh_token, expected_type="refresh")
        user = await self.repository.get_active_user_by_id(UUID(payload["sub"]))
        if not user:
            raise jwt_token._unauthorized("Пользователь неактивен")
        return Token(**await jwt_token.rotate_refresh_token(refresh_token))

    async def login_service(self, data: LogIn) -> Token:
        user = await self.repository.get_active_user_by_email(str(data.email))
        if not user or not await utils.verify_password(data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return Token(**await jwt_token.create_token_pair(str(user.user_id)))

    async def get_current_user(self, token: str) -> TokenData:
        payload = jwt_token.decode_token(token, expected_type="access")
        try:
            user_id = UUID(payload["sub"])
        except (TypeError, ValueError) as exc:
            raise jwt_token._unauthorized("Некорректный субъект токена") from exc

        user = await self.repository.get_active_user_by_id(user_id)
        if not user:
            raise jwt_token._unauthorized("Пользователь неактивен")
        return TokenData(user_id=user.user_id)

    async def get_user_profile(self, user_id: UUID) -> UserProfileOut:
        user = await self.repository.get_active_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return UserProfileOut.model_validate(user)

    async def logout_service(self, refresh_token: str, user_id: UUID) -> dict[str, str]:
        await jwt_token.revoke_refresh_token(refresh_token, str(user_id))
        return {"detail": "Вы успешно вышли из аккаунта"}
