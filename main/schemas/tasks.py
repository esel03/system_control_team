from datetime import datetime
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from main.db.models.tasks import Difficulty, Priority, Status


class TaskCreate(BaseModel):
    task_name: str = Field(min_length=1, max_length=200)
    task_text: str = Field(min_length=1, max_length=20_000)
    executor: UUID | None = None
    priority: Priority
    difficulty: Difficulty
    task_deadline_date: AwareDatetime | None = None

    @field_validator("task_name", "task_text", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class TaskUpdate(BaseModel):
    task_name: str | None = Field(default=None, min_length=1, max_length=200)
    task_text: str | None = Field(default=None, min_length=1, max_length=20_000)
    executor: UUID | None = None
    priority: Priority | None = None
    status: Status | None = None
    difficulty: Difficulty | None = None
    task_deadline_date: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_status_and_executor(self) -> "TaskUpdate":
        required_fields = ("task_name", "task_text", "priority", "status", "difficulty")
        for field_name in required_fields:
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(f"Поле {field_name} нельзя очистить")
        if self.status == Status.completed:
            raise ValueError("Для завершения задачи используйте endpoint complete")
        return self

    @field_validator("task_name", "task_text", mode="before")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class TaskOut(BaseModel):
    task_id: UUID


class TaskDetailsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: UUID
    task_id: UUID
    task_name: str
    task_text: str
    status: Status
    priority: Priority
    difficulty: Difficulty
    executor: UUID | None = None
    last_executor: UUID | None = None
    author: UUID
    task_update_author: UUID | None = None
    task_create_date: datetime
    task_update_date: datetime | None = None
    task_deadline_date: datetime | None = None
    task_finish_date: datetime | None = None


class TaskListOut(BaseModel):
    items: list[TaskDetailsOut]
    total: int
    limit: int
    offset: int


class TaskUserStatsOut(BaseModel):
    completed: int
    in_progress: int


class TaskTeamStatsOut(BaseModel):
    completed: int
    in_progress: int
