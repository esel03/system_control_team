from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel


class TaskCreate(BaseModel):
    team_id: uuid.UUID
    task_name: str
    task_text: str
    author: uuid.UUID
    executor: Optional[uuid.UUID] = None
    priority: str
    status: str
    difficulty: str
    task_create_date: Optional[datetime] = None
    task_update_date: Optional[datetime] = None
    task_deadline_date: Optional[datetime] = None
    task_finish_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    task_text: Optional[str] = None
    executor: Optional[uuid.UUID] = None
    task_update_author: Optional[uuid.UUID] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    difficulty: Optional[str] = None
    task_update_date: Optional[datetime] = None
    task_deadline_date: Optional[datetime] = None
    task_finish_date: Optional[datetime] = None


class TaskOut(BaseModel):
    task_id: uuid.UUID
