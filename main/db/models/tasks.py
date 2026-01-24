from sqlalchemy import TIMESTAMP, Boolean, Uuid, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SAEnum
import uuid
from main.db.base import Base
from enum import Enum
from datetime import datetime


class Priority(Enum):
    high = "срочно"
    medium = "средней срочности"
    low = "не является срочной"


class Difficulty(Enum):
    critical_high = "критически высокая"
    high = "высокая"
    medium = "средняя"
    low = "низкая"
    unknowed = "неизвестная"


class Status(Enum):
    is_executor = "есть исполнитель"
    is_not_executor = "нет исполнителя"
    in_progress = "в процессе"
    completed = "завершена"
    canceled = "отменена"


class Task(Base):
    __tablename__ = "tasks"

    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, comment="гуид задачи"
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("teams_to_rooms.team_id"),
        nullable=False,
        comment="гуид команды",
    )
    task_name: Mapped[str] = mapped_column(
        String, nullable=False, comment="название задачи"
    )
    task_text: Mapped[str] = mapped_column(
        String, nullable=False, comment="описание задачи"
    )
    author: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.user_id"), nullable=False, comment="Автор задачи"
    )
    executor: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.user_id"), nullable=True, comment="исполнитель задачи"
    )
    task_update_author: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.user_id"),
        nullable=True,
        comment="последний редактор задачи",
    )
    last_executor: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.user_id"),
        nullable=True,
        comment="предыдущий исполнитель задачи",
    )
    priority: Mapped[Priority] = mapped_column(
        SAEnum(Priority, byvalue=True), nullable=False, comment="приоритет"
    )
    status: Mapped[Status] = mapped_column(
        SAEnum(Status, byvalue=True), nullable=False, comment="статус задачи"
    )
    difficulty: Mapped[Difficulty] = mapped_column(
        SAEnum(Difficulty, byvalue=True), nullable=False, comment="сложность задачи"
    )
    task_create_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="дата создания задачи",
    )
    task_update_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, comment="текст обнолвения задачи"
    )
    task_deadline_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, comment="дедлайн задачи"
    )
    task_finish_date: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, comment="дата завершения задачи"
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, comment="флаг завершенности задачи", default=False
    )
