from __future__ import annotations

import os
from functools import lru_cache

from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, SQLModel, create_engine


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./assistant.db")
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


@lru_cache
def get_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    return scheduler


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    with Session(engine) as session:
        yield session
