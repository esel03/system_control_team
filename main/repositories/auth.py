from dataclasses import dataclass
from sqlalchemy import select, not_
from sqlalchemy.ext.asyncio import AsyncSession
from main.db.models.users import User
from uuid import UUID


@dataclass
class AuthRegUserRepository:
    db: AsyncSession

    async def get_email(self, email) -> str | None:
        stmt = (select(User.email)).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, data) -> str:
        stmt = User(**data.model_dump())
        self.db.add(stmt)
        await self.db.commit()
        await self.db.refresh(stmt)
        return stmt.email

    async def get_user(self, data) -> User | None:
        stmt = select(User).where(User.email == data.email, not_(User.is_deleted))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def info_user(self, user_id: UUID) :
        stmt = (select(User.email, User.last_name, User.first_name, User.patronymic_name)
                .where(User.user_id == user_id))
        return (await self.db.execute(stmt)).mappings().all()
