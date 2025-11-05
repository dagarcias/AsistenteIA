from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..models import Note, NoteCreate
from ..services.scheduler import SchedulerService
from ..deps import get_session

router = APIRouter()


@router.get("/", response_model=list[Note])
def list_notes(session: Session = Depends(get_session)) -> list[Note]:
    notes = session.exec(select(Note).order_by(Note.created_at.desc())).all()
    return notes


@router.post("/", response_model=Note, status_code=201)
def create_note(
    payload: NoteCreate,
    session: Session = Depends(get_session),
    scheduler: SchedulerService = Depends(SchedulerService.depends),
) -> Note:
    note = Note.from_orm(payload)
    session.add(note)
    session.commit()
    session.refresh(note)

    # Optionally schedule a reminder if recurrence provided through scheduler quick capture
    if payload.title and payload.title.lower().startswith("remind"):
        scheduler.schedule_note_ping(note)

    return note


@router.get("/{note_id}", response_model=Note)
def get_note(note_id: int, session: Session = Depends(get_session)) -> Note:
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, session: Session = Depends(get_session)) -> None:
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    session.delete(note)
    session.commit()


# placeholder dependency injection for scheduler service to avoid circular imports
