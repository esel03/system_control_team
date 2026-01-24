from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel
from enum import Enum


class Priority(str, Enum):
    pass


class TaskCreate(BaseModel):
    team_id: uuid.UUID
    task_name: str
    task_text: str
    executor: Optional[uuid.UUID] = None
    priority: str
    status: str
    difficulty: str
    task_deadline_date: Optional[datetime] = None
    task_finish_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    task_text: Optional[str] = None
    executor: Optional[uuid.UUID] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    difficulty: Optional[str] = None
    task_deadline_date: Optional[datetime] = None
    task_finish_date: Optional[datetime] = None


class TaskOut(BaseModel):
    task_id: uuid.UUID


class ListTasksOut(BaseModel):
    team_id: uuid.UUID
    task_id: uuid.UUID
    task_name: str
    status: str
    priority: str
    difficulty: str
    executor: Optional[uuid.UUID] = None
    last_executor: Optional[uuid.UUID] = None
    author: uuid.UUID
    task_create_date: datetime
    task_update_date: Optional[datetime] = None
    task_deadline_date: Optional[datetime] = None
    task_finish_date: Optional[datetime] = None
    is_completed: bool

    class Config:
        from_attributes = True


class ListTasksUserOut(BaseModel):
    team_id: uuid.UUID
    task_id: uuid.UUID
    task_name: str
    status: str
    priority: str
    difficulty: str
    author: uuid.UUID
    task_create_date: datetime
    task_update_date: Optional[datetime] = None
    task_deadline_date: Optional[datetime] = None
    task_finish_date: Optional[datetime] = None
    is_completed: bool

    class Config:
        from_attributes = True
