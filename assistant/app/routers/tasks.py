from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..models import Task, TaskCreate, TaskUpdate
from ..deps import get_session
from ..services.scheduler import SchedulerService

router = APIRouter()


@router.get("/", response_model=list[Task])
def list_tasks(
    include_completed: bool = Query(False, description="Include completed tasks"),
    session: Session = Depends(get_session),
) -> list[Task]:
    statement = select(Task)
    if not include_completed:
        statement = statement.where(Task.completed == False)  # noqa: E712
    statement = statement.order_by(Task.completed, Task.due_date, Task.priority.desc())
    return session.exec(statement).all()


@router.post("/", response_model=Task, status_code=201)
def create_task(
    payload: TaskCreate,
    session: Session = Depends(get_session),
    scheduler: SchedulerService = Depends(SchedulerService.depends),
) -> Task:
    task = Task.from_orm(payload)
    session.add(task)
    session.commit()
    session.refresh(task)
    scheduler.sync_task(task)
    return task


@router.patch("/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    session: Session = Depends(get_session),
    scheduler: SchedulerService = Depends(SchedulerService.depends),
) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    if task.completed:
        task.last_reminded_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    scheduler.sync_task(task)
    return task


@router.post("/{task_id}/complete", response_model=Task)
def complete_task(
    task_id: int,
    session: Session = Depends(get_session),
    scheduler: SchedulerService = Depends(SchedulerService.depends),
) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.completed = True
    task.last_reminded_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    scheduler.cancel_task(task.id)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    session: Session = Depends(get_session),
    scheduler: SchedulerService = Depends(SchedulerService.depends),
) -> None:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    scheduler.cancel_task(task_id)

