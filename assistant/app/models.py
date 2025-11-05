from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Field, SQLModel


class NoteBase(SQLModel):
    title: str = Field(index=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class Note(NoteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class NoteCreate(NoteBase):
    pass


class TaskBase(SQLModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = Field(default=None, index=True)
    priority: Optional[int] = Field(default=None, index=True)
    recurrence: Optional[str] = Field(default=None, description="Cron expression or shorthand like 'daily'")
    reminder_offset: Optional[int] = Field(
        default=None,
        description="Minutes before due_date to fire reminder. If recurrence provided this is applied to each run.",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    completed: bool = Field(default=False, index=True)
    last_reminded_at: Optional[datetime] = Field(default=None)


class Task(TaskBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = None
    recurrence: Optional[str] = None
    reminder_offset: Optional[int] = None
    completed: Optional[bool] = None
    last_reminded_at: Optional[datetime] = None


class Reminder(SQLModel):
    task_id: int
    run_at: datetime
    recurrence: Optional[str] = None

    @property
    def eta(self) -> timedelta:
        return self.run_at - datetime.utcnow()
