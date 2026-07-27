import uuid

from sqlalchemy import Boolean, Index, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

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
    patronymic_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="отчество пользователя"
    )
    password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="хеш пароля пользователя"
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="флаг удаления пользователя",
    )

    __table_args__ = (Index("uix_users_email_lower", func.lower(email), unique=True),)
