from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from sqlmodel import Session, select

from .deps import engine, init_db
from .models import Note, NoteCreate, Task, TaskCreate
from .utils.timeparse import parse_when

app = typer.Typer(help="Quick capture CLI for notes and tasks")


def _save(instance) -> None:
    with Session(engine) as session:
        session.add(instance)
        session.commit()
        session.refresh(instance)


@app.command()
def note(title: str, content: str) -> None:
    """Create a note quickly."""
    init_db()
    note = Note.from_orm(NoteCreate(title=title, content=content))
    _save(note)
    typer.echo(f"Note saved with id={note.id}")


def _parse_due(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return parse_when(value)


@app.command()
def task(
    title: str,
    description: Optional[str] = typer.Option(None, "--description", "-d"),
    due: Optional[str] = typer.Option(None, "--due"),
    priority: Optional[int] = typer.Option(None, "--priority", "-p"),
    recurrence: Optional[str] = typer.Option(None, "--recurrence", "-r"),
    reminder_offset: Optional[int] = typer.Option(None, "--reminder", "-m"),
) -> None:
    """Create a task quickly."""
    init_db()
    payload = TaskCreate(
        title=title,
        description=description,
        due_date=_parse_due(due),
        priority=priority,
        recurrence=recurrence,
        reminder_offset=reminder_offset,
    )
    task = Task.from_orm(payload)
    _save(task)
    typer.echo(f"Task saved with id={task.id}")


@app.command()
def export(out: Path = typer.Argument(Path("assistant_export.json"))) -> None:
    """Dump all notes and tasks to JSON."""
    init_db()
    with Session(engine) as session:
        notes = session.exec(select(Note)).all()
        tasks = session.exec(select(Task)).all()
        data = {
            "notes": [note.dict() for note in notes],
            "tasks": [task.dict() for task in tasks],
        }
        out.write_text(json.dumps(data, default=str, indent=2))
        typer.echo(f"Exported to {out}")


if __name__ == "__main__":
    app()
