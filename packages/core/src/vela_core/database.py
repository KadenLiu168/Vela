from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE_URL = "sqlite+pysqlite:///vela.db"


def create_engine_from_url(database_url: str, **kwargs: Any) -> Engine:
    engine = create_engine(database_url, **kwargs)
    if engine.url.drivername.startswith("sqlite"):
        # WAL lets readers (API list/detail/poll) observe committed rows while
        # a long walk-forward `complete()` write transaction is open. The
        # default rollback journal blocks every reader for the full duration of
        # the multi-minute write, so the run-trigger endpoint cannot satisfy
        # the concurrent-run guard (HTTP 409) nor let the frontend poll the
        # running status.
        @event.listens_for(engine, "connect")
        def _set_sqlite_wal_pragma(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    return engine


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
