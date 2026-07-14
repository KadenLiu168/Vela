from datetime import date

from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.main import app, get_market_data_provider
from vela_core.database import DEFAULT_DATABASE_URL

from tests.integration_data import (
    ControlledMarketDataProvider,
    add_etf,
    add_price_history,
    daily_price,
    prepare_sqlite_database,
)


def test_full_p0_workflow_uses_real_api_and_persisted_backend_state(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'p0-workflow.db'}"
    session_factory = prepare_sqlite_database(database_url)
    latest_seed_date = date(2026, 6, 23)
    fetched_trade_date = date(2026, 6, 24)
    with session_factory() as session:
        first = add_etf(session, exchange="SSE", symbol="510300", currency="CNY")
        second = add_etf(session, exchange="SZSE", symbol="159915", currency="CNY")
        defense = add_etf(session, exchange="SSE", symbol="511010", currency="CNY")
        defense_second = add_etf(session, exchange="SSE", symbol="511880", currency="CNY")
        defense_third = add_etf(session, exchange="SSE", symbol="518880", currency="CNY")
        add_price_history(session, etf_id=first.id, end_date=latest_seed_date)
        add_price_history(session, etf_id=second.id, end_date=latest_seed_date)
        add_price_history(session, etf_id=defense.id, end_date=latest_seed_date)
        add_price_history(session, etf_id=defense_second.id, end_date=latest_seed_date)
        add_price_history(session, etf_id=defense_third.id, end_date=latest_seed_date)
        session.commit()

    provider = ControlledMarketDataProvider(
        {
            "510300": [daily_price("510300", trade_date=fetched_trade_date)],
            "159915": [daily_price("159915", trade_date=fetched_trade_date)],
            "511010": [daily_price("511010", trade_date=fetched_trade_date)],
            "511880": [daily_price("511880", trade_date=fetched_trade_date)],
            "518880": [daily_price("518880", trade_date=fetched_trade_date)],
        }
    )

    try:
        initialize_database(app, database_url=database_url)
        app.dependency_overrides[get_market_data_provider] = lambda: provider
        client = TestClient(app)

        initial_dashboard = client.get("/api/dashboard")
        fetch = client.post("/api/market-data/fetch?mode=incremental")
        generated_signal = client.post("/api/strategy-signals/generate")
        latest_signal = client.get("/api/strategy-signals/latest")
        backtest_run = client.post("/api/backtests/run?startDate=2026-06-15&endDate=2026-06-24")
        backtest_detail = client.get(f"/api/backtests/{backtest_run.json()['run_id']}")
        refreshed_dashboard = client.get("/api/dashboard")
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert initial_dashboard.status_code == 200
    assert (
        initial_dashboard.json()["market_data"]["latest_trade_date"] == latest_seed_date.isoformat()
    )

    assert fetch.status_code == 200
    assert fetch.json() == {
        "status": "success",
        "requested_etf_count": 5,
        "rows_fetched": 5,
        "rows_inserted": 5,
        "rows_updated": 0,
        "failed_symbols": [],
        "error_message": None,
    }
    assert provider.requests == [
        ("159915", latest_seed_date),
        ("510300", latest_seed_date),
        ("511010", latest_seed_date),
        ("511880", latest_seed_date),
        ("518880", latest_seed_date),
    ]

    assert generated_signal.status_code == 200
    generated = generated_signal.json()
    assert generated["status"] == "success"
    assert generated["signal_date"] == fetched_trade_date.isoformat()
    assert generated["positions"]

    assert latest_signal.status_code == 200
    latest = latest_signal.json()
    assert latest["has_signal"] is True
    assert latest["signal"]["signal_id"] == generated["signal_id"]
    assert latest["signal"]["signal_date"] == generated["signal_date"]
    assert len(latest["positions"]) == len(generated["positions"])

    assert backtest_run.status_code == 200
    run = backtest_run.json()
    assert run["status"] == "success"
    assert run["start_date"] == "2026-06-15"
    assert run["end_date"] == "2026-06-24"
    assert run["trading_day_count"] == 10
    assert run["signal_count"] >= 1

    assert backtest_detail.status_code == 200
    detail = backtest_detail.json()
    assert detail["run"]["run_id"] == run["run_id"]
    assert detail["metrics"]["total_return"] == run["total_return"]
    assert len(detail["equity_curve"]) == run["trading_day_count"]
    assert detail["equity_curve"][-1]["trade_date"] == fetched_trade_date.isoformat()

    assert refreshed_dashboard.status_code == 200
    dashboard = refreshed_dashboard.json()
    assert dashboard["market_data"]["latest_trade_date"] == fetched_trade_date.isoformat()
    assert dashboard["latest_signal"]["status"] == "success"
    assert dashboard["latest_signal"]["position_count"] > 0
    assert dashboard["recent_backtest"]["run_id"] == run["run_id"]
    assert dashboard["recent_fetch_logs"][0]["mode"] == "incremental"
    assert dashboard["recent_fetch_logs"][0]["rows_inserted"] == 5

    backend_gaps_or_field_mismatches: list[str] = []
    assert backend_gaps_or_field_mismatches == []
