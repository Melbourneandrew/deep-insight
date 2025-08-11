from __future__ import annotations

import os
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine


def _get_database_url() -> str:
    # Prefer env var; fallback to Alembic's default if present
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    # Defaults to local Postgres matching alembic.ini
    return "postgresql+psycopg://postgres:postgres@localhost:5432/app"


DATABASE_URL = _get_database_url()
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_size=200,
    max_overflow=50
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
