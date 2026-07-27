import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import TIMESTAMP, CheckConstraint, ForeignKey, Index, String, Uuid, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from main.db.base import Base


class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Difficulty(str, Enum):
    critical_high = "critical_high"
    high = "high"
    medium = "medium"
    low = "low"
    unknown = "unknown"


class Status(str, Enum):
    assigned = "assigned"
    unassigned = "unassigned"
    in_progress = "in_progress"
    completed = "completed"
    canceled = "canceled"


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
        SAEnum(
            Priority,
            name="priority",
            values_callable=lambda enum: [member.value for member in enum],
            validate_strings=True,
        ),
        nullable=False,
        comment="приоритет",
    )
    status: Mapped[Status] = mapped_column(
        SAEnum(
            Status,
            name="status",
            values_callable=lambda enum: [member.value for member in enum],
            validate_strings=True,
        ),
        nullable=False,
        comment="статус задачи",
    )
    difficulty: Mapped[Difficulty] = mapped_column(
        SAEnum(
            Difficulty,
            name="difficulty",
            values_callable=lambda enum: [member.value for member in enum],
            validate_strings=True,
        ),
        nullable=False,
        comment="сложность задачи",
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
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, comment="дата мягкого удаления"
    )
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.user_id"),
        nullable=True,
        comment="пользователь, удаливший задачу",
    )

    __table_args__ = (
        CheckConstraint(
            "(status NOT IN ('assigned', 'in_progress') OR executor IS NOT NULL) "
            "AND (status <> 'unassigned' OR executor IS NULL)",
            name="ck_tasks_status_executor",
        ),
        CheckConstraint(
            "status <> 'completed' OR task_finish_date IS NOT NULL",
            name="ck_tasks_completed_finish",
        ),
        Index("ix_tasks_team_status", "team_id", "status"),
        Index("ix_tasks_executor_status", "executor", "status"),
        Index("ix_tasks_team_finish_date", "team_id", "task_finish_date"),
    )
