from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Uuid, String, Boolean
import uuid
from main.db.base import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, comment="id пользователя"
    )
    email: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, comment="email пользователя"
    )
    first_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="имя пользователя"
    )
    last_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="фамилия пользователя"
    )
    patronymic_name: Mapped[str] = mapped_column(
        String(100), comment="отчество пользователя"
    )
    password: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="пароль пользователя"
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="флаг удаленности пользователя"
    )
