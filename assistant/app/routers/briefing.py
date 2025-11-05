from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..deps import get_session
from ..models import Note, Task

router = APIRouter()


@router.get("/today")
def daily_briefing(session: Session = Depends(get_session)) -> dict[str, object]:
    now = datetime.utcnow()
    start_of_day = datetime(now.year, now.month, now.day)
    end_of_day = start_of_day + timedelta(days=1)

    due_today = session.exec(
        select(Task).where(
            Task.completed == False,  # noqa: E712
            Task.due_date.is_not(None),
            Task.due_date >= start_of_day,
            Task.due_date < end_of_day,
        )
    ).all()

    overdue = session.exec(
        select(Task).where(
            Task.completed == False,  # noqa: E712
            Task.due_date.is_not(None),
            Task.due_date < start_of_day,
        )
    ).all()

    upcoming = session.exec(
        select(Task)
        .where(
            Task.completed == False,  # noqa: E712
            Task.due_date.is_not(None),
            Task.due_date >= end_of_day,
            Task.due_date < end_of_day + timedelta(days=7),
        )
        .order_by(Task.due_date)
    ).all()

    latest_notes = session.exec(select(Note).order_by(Note.created_at.desc()).limit(5)).all()

    priorities = sorted(
        [task for task in due_today + upcoming if task.priority is not None],
        key=lambda task: task.priority,
    )

    return {
        "timestamp": now.isoformat(),
        "due_today": due_today,
        "overdue": overdue,
        "upcoming": upcoming,
        "latest_notes": latest_notes,
        "priorities": priorities[:5],
    }
