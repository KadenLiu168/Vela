from collections.abc import Sequence
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.main import app, get_market_data_provider
from vela_core import ConfigError, DailyPrice
from vela_core.database import DEFAULT_DATABASE_URL

from tests.integration_data import add_etf, prepare_sqlite_database


def test_validation_error_uses_stable_error_envelope(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'validation-error.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).post("/api/market-data/fetch?mode=recent")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "validation_error",
            "category": "validation",
            "message": "Request validation failed",
        }
    }


def test_not_found_error_uses_stable_error_envelope(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'not-found-error.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/backtests/999")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "not_found",
            "category": "not_found",
            "message": "Backtest run not found",
        }
    }


def test_no_market_data_error_uses_stable_error_envelope(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'no-market-data-error.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).post("/api/strategy-signals/generate")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "no_market_data",
            "category": "operation_failed",
            "message": "No local market prices found",
        }
    }


def test_invalid_date_range_error_uses_stable_error_envelope(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'invalid-date-error.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).post(
            "/api/backtests/run?startDate=2026-01-10&endDate=2026-01-01"
        )
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "invalid_date_range",
            "category": "operation_failed",
            "message": "start_date must be on or before end_date",
        }
    }


def test_config_error_uses_stable_error_envelope(monkeypatch) -> None:
    def raise_config_error() -> dict[str, object]:
        raise ConfigError(
            "Failed to read configuration file config/missing.yaml",
            path=Path("config/missing.yaml"),
        )

    monkeypatch.setattr(
        "vela_api.system_router.get_config_summary", lambda _config: raise_config_error()
    )

    response = TestClient(app, raise_server_exceptions=False).get("/api/config")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "config_error",
            "category": "operation_failed",
            "message": "Failed to read configuration file config/missing.yaml",
        }
    }


def test_provider_workflow_failure_keeps_stable_fetch_response(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'provider-error.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        add_etf(session, symbol="SPY")
        session.commit()

    try:
        initialize_database(app, database_url=database_url)
        app.dependency_overrides[get_market_data_provider] = lambda: FailingMarketDataProvider()

        response = TestClient(app).post("/api/market-data/fetch?mode=full")
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json() == {
        "status": "failed",
        "requested_etf_count": 1,
        "rows_fetched": 0,
        "rows_inserted": 0,
        "rows_updated": 0,
        "failed_symbols": ["SPY"],
        "error_message": "SPY: provider unavailable",
    }


def test_unexpected_error_uses_stable_error_envelope() -> None:
    def raise_unexpected_error() -> object:
        raise RuntimeError("database unavailable")

    try:
        app.dependency_overrides[get_market_data_provider] = raise_unexpected_error

        response = TestClient(app, raise_server_exceptions=False).post(
            "/api/market-data/fetch?mode=full"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "unexpected_error",
            "category": "unexpected",
            "message": "Unexpected API error",
        }
    }


class FailingMarketDataProvider:
    name = "failing"

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        raise RuntimeError("provider unavailable")
