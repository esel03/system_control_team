from dataclasses import dataclass
from main.schemas.auth import RegistrationIn
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from main.db.models.users import User


@dataclass
class AuthRegUserRepository:
    db: AsyncSession

    async def get_email(self, email):
        stmt = (select(User.email)).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, data: RegistrationIn):
        stmt = User(**data.model_dump())
        self.db.add(stmt)
        await self.db.commit()
        await self.db.refresh(stmt)
        return stmt.user_id
