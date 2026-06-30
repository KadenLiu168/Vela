import pytest
from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session
from vela_api.database import get_database_session, initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL, create_engine_from_url, create_session_factory

DATABASE_SESSION = Depends(get_database_session)


def _build_database_url(tmp_path) -> str:
    return f"sqlite+pysqlite:///{tmp_path / 'api-test.db'}"


def test_api_app_uses_default_database_session_factory() -> None:
    assert str(app.state.session_factory.kw["bind"].url) == DEFAULT_DATABASE_URL


def test_api_database_session_commits_successful_request(tmp_path) -> None:
    engine = create_engine_from_url(_build_database_url(tmp_path))
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE events (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"))

    test_app = FastAPI()
    test_app.state.session_factory = create_session_factory(engine)

    @test_app.post("/events")
    def create_event(session: Session = DATABASE_SESSION) -> dict[str, str]:
        session.execute(text("INSERT INTO events (name) VALUES ('created')"))
        return {"status": "created"}

    response = TestClient(test_app).post("/events")

    assert response.status_code == 200
    with engine.connect() as connection:
        count = connection.execute(text("SELECT COUNT(*) FROM events")).scalar_one()
    assert count == 1


def test_api_database_session_rolls_back_failed_request(tmp_path) -> None:
    engine = create_engine_from_url(_build_database_url(tmp_path))
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE events (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"))

    test_app = FastAPI()
    test_app.state.session_factory = create_session_factory(engine)

    @test_app.post("/events")
    def create_event(session: Session = DATABASE_SESSION) -> None:
        session.execute(text("INSERT INTO events (name) VALUES ('failed')"))
        raise RuntimeError("force rollback")

    with pytest.raises(RuntimeError, match="force rollback"):
        TestClient(test_app).post("/events")

    with engine.connect() as connection:
        count = connection.execute(text("SELECT COUNT(*) FROM events")).scalar_one()
    assert count == 0


def test_initialize_database_sets_session_factory_from_database_url(tmp_path) -> None:
    test_app = FastAPI()
    database_url = _build_database_url(tmp_path)

    initialize_database(test_app, database_url=database_url)

    assert str(test_app.state.session_factory.kw["bind"].url) == database_url


def test_api_production_routes_include_read_only_dashboard_endpoint() -> None:
    routes = {
        (route.path, tuple(sorted(route.methods or ())))
        for route in app.routes
        if isinstance(route, APIRoute) and route.include_in_schema
    }

    assert routes == {
        ("/api/config", ("GET",)),
        ("/api/dashboard", ("GET",)),
        ("/api/health", ("GET",)),
        ("/api/market-data/fetch", ("POST",)),
        ("/api/strategy-signals/generate", ("POST",)),
    }
