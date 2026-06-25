import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from vela_core.database import (
    DEFAULT_DATABASE_URL,
    create_engine_from_url,
    create_session_factory,
    managed_session,
)


class TrackingSession(Session):
    committed: bool
    rolled_back: bool
    closed: bool

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def commit(self) -> None:
        self.committed = True
        super().commit()

    def rollback(self) -> None:
        self.rolled_back = True
        super().rollback()

    def close(self) -> None:
        self.closed = True
        super().close()


def test_create_engine_from_url_returns_engine() -> None:
    engine = create_engine_from_url("sqlite+pysqlite:///:memory:")

    assert isinstance(engine, Engine)
    assert str(engine.url) == "sqlite+pysqlite:///:memory:"


def test_default_database_url_uses_local_sqlite_database() -> None:
    assert DEFAULT_DATABASE_URL == "sqlite+pysqlite:///vela.db"


def test_create_session_factory_binds_sessions_to_engine() -> None:
    engine = create_engine_from_url("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(engine)

    session = session_factory()
    try:
        assert session.bind is engine
    finally:
        session.close()


def test_managed_session_commits_successful_work_and_closes_session() -> None:
    engine = create_engine_from_url("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(engine, class_=TrackingSession)

    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"))

    tracked_session: TrackingSession
    with managed_session(session_factory) as session:
        assert isinstance(session, TrackingSession)
        session.execute(text("INSERT INTO items (name) VALUES ('SPY')"))
        tracked_session = session

    with engine.connect() as connection:
        count = connection.execute(text("SELECT COUNT(*) FROM items")).scalar_one()

    assert count == 1
    assert tracked_session.committed is True
    assert tracked_session.rolled_back is False
    assert tracked_session.closed is True


def test_managed_session_rolls_back_failed_work_closes_and_reraises() -> None:
    engine = create_engine_from_url("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(engine, class_=TrackingSession)

    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"))

    tracked_session: TrackingSession
    with pytest.raises(RuntimeError, match="force rollback"):
        with managed_session(session_factory) as session:
            assert isinstance(session, TrackingSession)
            session.execute(text("INSERT INTO items (name) VALUES ('QQQ')"))
            tracked_session = session
            raise RuntimeError("force rollback")

    with engine.connect() as connection:
        count = connection.execute(text("SELECT COUNT(*) FROM items")).scalar_one()

    assert count == 0
    assert tracked_session.committed is False
    assert tracked_session.rolled_back is True
    assert tracked_session.closed is True


def test_managed_session_closes_after_read_only_work() -> None:
    engine = create_engine_from_url("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(engine, class_=TrackingSession)

    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"))

    tracked_session: TrackingSession
    with managed_session(session_factory) as session:
        assert isinstance(session, TrackingSession)
        count = session.execute(text("SELECT COUNT(*) FROM items")).scalar_one()
        tracked_session = session

    assert count == 0
    assert tracked_session.committed is True
    assert tracked_session.rolled_back is False
    assert tracked_session.closed is True
