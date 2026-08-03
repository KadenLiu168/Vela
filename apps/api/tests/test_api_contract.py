from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.main import app, get_market_data_provider
from vela_core import ConfigError, DailyPrice
from vela_core.database import DEFAULT_DATABASE_URL

from tests.integration_data import (
    ControlledMarketDataProvider,
    add_etf,
    add_price_history,
    daily_price,
    prepare_sqlite_database,
    prepare_workflow_database,
)


def test_first_version_api_success_response_contracts(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'api-contract-success.db'}"
    dataset = prepare_workflow_database(database_url)
    session_factory = prepare_sqlite_database(database_url, reset=False)
    with session_factory() as session:
        add_price_history(session, etf_id=dataset.first_etf_id, end_date=date(2026, 1, 10))
        add_price_history(session, etf_id=dataset.second_etf_id, end_date=date(2026, 1, 10))
        add_price_history(session, etf_id=dataset.defensive_etf_id, end_date=date(2026, 1, 10))
        session.commit()
    provider = ControlledMarketDataProvider(
        {
            "510300": [daily_price("510300", trade_date=date(2026, 6, 24))],
            "159915": [daily_price("159915", trade_date=date(2026, 6, 24))],
            "511010": [daily_price("511010", trade_date=date(2026, 6, 24))],
        }
    )

    with _configured_api(database_url, provider=provider):
        client = TestClient(app)

        health = client.get("/api/health")
        config = client.get("/api/config")
        dashboard = client.get("/api/dashboard")
        fetch = client.post("/api/market-data/fetch?mode=incremental")
        generated_signal = client.post("/api/strategy-signals/generate")
        latest_signal = client.get("/api/strategy-signals/latest")
        backtest_list = client.get("/api/backtests")
        backtest_run = client.post("/api/backtests/run?startDate=2026-01-01&endDate=2026-01-10")
        backtest_detail = client.get(f"/api/backtests/{dataset.backtest_run_id}")

    assert health.status_code == 200
    assert health.json() == {"status": "healthy"}

    assert config.status_code == 200
    assert {"strategy", "etf_pool"} <= config.json().keys()

    assert dashboard.status_code == 200
    assert {
        "strategy",
        "market_data",
        "latest_signal",
        "recent_backtest",
        "recent_fetch_logs",
    } <= dashboard.json().keys()

    assert fetch.status_code == 200
    assert set(fetch.json()) == {
        "status",
        "requested_etf_count",
        "rows_fetched",
        "rows_inserted",
        "rows_updated",
        "failed_symbols",
        "error_message",
    }

    assert generated_signal.status_code == 200
    assert set(generated_signal.json()) == {
        "signal_id",
        "signal_date",
        "config_version",
        "status",
        "result",
        "error_message",
        "source",
        "positions",
    }

    assert latest_signal.status_code == 200
    assert {"has_signal", "signal", "positions"} <= latest_signal.json().keys()

    assert backtest_list.status_code == 200
    assert "runs" in backtest_list.json()

    assert backtest_run.status_code == 200
    assert set(backtest_run.json()) == {
        "run_id",
        "status",
        "start_date",
        "end_date",
        "trading_day_count",
        "signal_count",
        "total_return",
        "annualized_return",
        "max_drawdown",
        "volatility",
        "sharpe_ratio",
        "benchmarks",
    }

    assert backtest_detail.status_code == 200
    assert {"run", "metrics", "equity_curve"} <= backtest_detail.json().keys()


def test_api_empty_state_response_contracts(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'api-contract-empty.db'}"
    prepare_sqlite_database(database_url)

    with _configured_api(database_url):
        client = TestClient(app)
        dashboard = client.get("/api/dashboard")
        latest_signal = client.get("/api/strategy-signals/latest")
        backtest_list = client.get("/api/backtests")

    assert dashboard.status_code == 200
    assert dashboard.json()["market_data"] == {
        "price_rows": 0,
        "covered_etfs": 0,
        "earliest_trade_date": None,
        "latest_trade_date": None,
        "etf_list": [],
    }
    assert dashboard.json()["latest_signal"] is None
    assert dashboard.json()["recent_backtest"] is None

    assert latest_signal.status_code == 200
    assert latest_signal.json() == {
        "has_signal": False,
        "signal": None,
        "positions": [],
    }

    assert backtest_list.status_code == 200
    assert backtest_list.json() == {"runs": []}


def test_api_error_response_contracts(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'api-contract-errors.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        add_etf(session, symbol="SPY")
        session.commit()

    with _configured_api(database_url, provider=FailingMarketDataProvider()):
        client = TestClient(app, raise_server_exceptions=False)

        validation = client.post("/api/market-data/fetch?mode=recent")
        not_found = client.get("/api/backtests/999")
        missing_market_data = client.post("/api/strategy-signals/generate")
        invalid_date_range = client.post(
            "/api/backtests/run?startDate=2026-01-10&endDate=2026-01-01"
        )
        provider_failure = client.post("/api/market-data/fetch?mode=full")

        def raise_config_error(_config: object) -> dict[str, object]:
            raise ConfigError(
                "Failed to read configuration file config/missing.yaml",
                path=Path("config/missing.yaml"),
            )

        monkeypatch.setattr("vela_api.system_router.get_config_summary", raise_config_error)
        config_failure = client.get("/api/config")

    assert validation.status_code == 422
    assert validation.json()["error"] == {
        "code": "validation_error",
        "category": "validation",
        "message": "Request validation failed",
    }

    assert not_found.status_code == 404
    assert not_found.json()["error"] == {
        "code": "not_found",
        "category": "not_found",
        "message": "Backtest run not found",
    }

    assert missing_market_data.status_code == 400
    assert missing_market_data.json()["error"] == {
        "code": "no_market_data",
        "category": "operation_failed",
        "message": "No local market prices found",
    }

    assert invalid_date_range.status_code == 400
    assert invalid_date_range.json()["error"] == {
        "code": "invalid_date_range",
        "category": "operation_failed",
        "message": "start_date must be on or before end_date",
    }

    assert provider_failure.status_code == 200
    assert provider_failure.json() == {
        "status": "failed",
        "requested_etf_count": 1,
        "rows_fetched": 0,
        "rows_inserted": 0,
        "rows_updated": 0,
        "failed_symbols": ["SPY"],
        "error_message": "SPY: SPY unavailable",
    }

    assert config_failure.status_code == 500
    assert config_failure.json()["error"] == {
        "code": "config_error",
        "category": "operation_failed",
        "message": "Failed to read configuration file config/missing.yaml",
    }


@contextmanager
def _configured_api(
    database_url: str,
    *,
    provider: object | None = None,
) -> Iterator[None]:
    try:
        initialize_database(app, database_url=database_url)
        if provider is not None:
            app.dependency_overrides[get_market_data_provider] = lambda: provider
        yield
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)


class FailingMarketDataProvider:
    name = "failing"

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        raise RuntimeError(f"{symbol} unavailable")


def test_openapi_declares_concrete_success_schemas_for_every_api_route() -> None:
    openapi = app.openapi()

    for operations in openapi["paths"].values():
        for operation in operations.values():
            response_schema = operation["responses"]["200"]
            schema = response_schema["content"]["application/json"]["schema"]
            assert "$ref" in schema

    for schema in openapi["components"]["schemas"].values():
        assert not _has_unconstrained_object(schema)


def _has_unconstrained_object(value: object) -> bool:
    if isinstance(value, dict):
        if value.get("additionalProperties") is True:
            return True
        return any(_has_unconstrained_object(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_unconstrained_object(item) for item in value)
    return False
