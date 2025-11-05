from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Callable

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from fastapi import Depends
from sqlmodel import Session

from ..deps import engine, get_scheduler, get_session
from ..models import Note, Task
from ..utils.timeparse import parse_when

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, scheduler=None) -> None:
        self.scheduler = scheduler or get_scheduler()

    @classmethod
    def depends(cls, session: Session = Depends(get_session)) -> "SchedulerService":  # type: ignore[unused-ignore]
        # Session dependency ensures the DB is initialised for request handlers
        session.close()
        return cls()

    def schedule_note_ping(self, note: Note) -> None:
        run_at = parse_when(note.content)
        if not run_at:
            return
        self.scheduler.add_job(
            func=self._notify,
            trigger=DateTrigger(run_date=run_at),
            args=[f"Reminder from note '{note.title}'", note.content],
            id=f"note-{note.id}-{run_at.timestamp()}",
            replace_existing=True,
        )
        logger.info("Scheduled reminder for note %s at %s", note.id, run_at)

    def sync_task(self, task: Task) -> None:
        self.cancel_task(task.id)
        if task.completed:
            return
        next_run = None
        if task.due_date:
            run_time = task.due_date
            if task.reminder_offset:
                run_time = run_time - timedelta(minutes=task.reminder_offset)
            if run_time > datetime.utcnow():
                next_run = run_time
        if not next_run and task.recurrence:
            trigger = self._parse_recurrence(task.recurrence)
            if trigger:
                job_id = f"task-{task.id}-recurring"
                self.scheduler.add_job(
                    func=self._notify_task,
                    trigger=trigger,
                    args=[task.id],
                    id=job_id,
                    replace_existing=True,
                )
                logger.info("Scheduled recurring task %s with trigger %s", task.id, trigger)
            return
        if next_run:
            job_id = f"task-{task.id}-once"
            self.scheduler.add_job(
                func=self._notify_task,
                trigger=DateTrigger(run_date=next_run),
                args=[task.id],
                id=job_id,
                replace_existing=True,
            )
            logger.info("Scheduled one-shot task %s at %s", task.id, next_run)

    def cancel_task(self, task_id: int) -> None:
        for suffix in ("-once", "-recurring"):
            job_id = f"task-{task_id}{suffix}"
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                continue

    def _notify_task(self, task_id: int) -> None:
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                logger.warning("Task %s not found for notification", task_id)
                return
            self._notify(f"Task reminder: {task.title}", task.description or "")
            task.last_reminded_at = datetime.utcnow()
            session.add(task)
            session.commit()

    def _notify(self, title: str, body: str) -> None:
        logger.info("[NOTIFY] %s - %s", title, body)
        print(f"\n🔔 {title}: {body}\n", flush=True)

    def _parse_recurrence(self, recurrence: str) -> CronTrigger | None:
        recurrence = recurrence.strip().lower()
        presets = {
            "daily": CronTrigger(hour=9),
            "weekly": CronTrigger(day_of_week="mon", hour=9),
            "weekdays": CronTrigger(day_of_week="mon-fri", hour=9),
        }
        if recurrence in presets:
            return presets[recurrence]
        try:
            return CronTrigger.from_crontab(recurrence)
        except ValueError:
            logger.warning("Invalid recurrence pattern '%s'", recurrence)
            return None
