"""Engine and session helpers."""

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine


def get_engine(database_url: str, echo: bool = False) -> Engine:
    """Return a SQLAlchemy engine configured for SQLite or other backends."""
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, echo=echo, connect_args=connect_args)


def init_db(engine: Engine) -> None:
    """Create database tables if they do not exist."""
    SQLModel.metadata.create_all(engine)


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    with Session(engine) as session:
        yield session

