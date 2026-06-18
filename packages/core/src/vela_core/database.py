from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def create_engine_from_url(database_url: str, **kwargs: Any) -> Engine:
    return create_engine(database_url, **kwargs)


def create_session_factory(engine: Engine, **kwargs: Any) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, **kwargs)


@contextmanager
def managed_session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
