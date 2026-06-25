from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session
from vela_core.database import (
    DEFAULT_DATABASE_URL,
    create_engine_from_url,
    create_session_factory,
    managed_session,
)


def initialize_database(app, database_url: str = DEFAULT_DATABASE_URL) -> None:
    engine = create_engine_from_url(database_url)
    app.state.session_factory = create_session_factory(engine)


def get_database_session(request: Request) -> Iterator[Session]:
    with managed_session(request.app.state.session_factory) as session:
        yield session
