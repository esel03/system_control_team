from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from main.db.models.users import User
from main.schemas.auth import RegistrationIn


@dataclass
class AuthRegUserRepository:
    db: AsyncSession

    async def get_email(self, email: str) -> str | None:
        stmt = select(User.email).where(func.lower(User.email) == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, data: RegistrationIn) -> str:
        user = User(**data.model_dump())
        self.db.add(user)
        await self.db.flush()
        return user.email

    async def get_active_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(
            func.lower(User.email) == email.lower(),
            User.is_deleted.is_(False),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_user_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(
            User.user_id == user_id,
            User.is_deleted.is_(False),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
