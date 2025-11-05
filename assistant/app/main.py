from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .deps import get_scheduler, init_db
from .routers import ask, briefing, notes, tasks

logger = logging.getLogger("assistant.app")


@asynccontextmanager
def lifespan(app: FastAPI):
    init_db()
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")
    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler shut down")


app = FastAPI(title="Personal Assistant", lifespan=lifespan)

app.include_router(notes.router, prefix="/notes", tags=["notes"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(briefing.router, prefix="/briefing", tags=["briefing"])
app.include_router(ask.router, prefix="/ask", tags=["ask"])


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
