from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class TaskCreate(BaseModel):
    team_id: UUID
    task_name: str
    task_text: str
    executor: Optional[UUID] = None
    priority: str
    status: str
    difficulty: str
    task_deadline_date: Optional[datetime] = None
    task_finish_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    task_text: Optional[str] = None
    executor: Optional[UUID] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    difficulty: Optional[str] = None
    task_deadline_date: Optional[datetime] = None
    task_finish_date: Optional[datetime] = None


class TaskOut(BaseModel):
    task_id: UUID


class ListTasksOut(BaseModel):
    team_id: UUID
    task_id: UUID
    task_name: str
    task_text: str
    status: str
    priority: str
    difficulty: str
    executor: Optional[UUID] = None
    last_executor: Optional[UUID] = None
    author: UUID
    task_create_date: datetime
    task_update_date: Optional[datetime] = None
    task_deadline_date: Optional[datetime] = None
    task_finish_date: Optional[datetime] = None
    is_completed: bool

    class Config:
        from_attributes = True


class TaskUserStatsOut(BaseModel):
    completed: int
    in_progress: int


class TaskTeamStatsOut(BaseModel):
    completed: int
    in_progress: int
