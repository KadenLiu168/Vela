import json

import vela_core.market_data_fetcher as market_data_fetcher
from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.dependencies import get_app_config
from vela_api.main import app, get_market_data_provider
from vela_core import load_app_config
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.market_price_mapping import to_market_price
from vela_core.models import TradingCalendar

from tests.integration_data import (
    ControlledMarketDataProvider,
    add_etf,
    canonical_etf_pool,
    canonical_provider_prices,
    canonical_strategy_config,
    canonical_workflow_sessions,
    prepare_sqlite_database,
)


def test_full_p0_workflow_uses_real_api_and_persisted_backend_state(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'p0-workflow.db'}"
    session_factory = prepare_sqlite_database(database_url)
    sessions = canonical_workflow_sessions()
    config = canonical_strategy_config()
    app_config = load_app_config("config/strategy_v1.yaml").model_copy(update={"strategy": config})
    pool = canonical_etf_pool()
    provider = ControlledMarketDataProvider(canonical_provider_prices(sessions))
    etf_ids: dict[str, int] = {}
    with session_factory() as session:
        for etf in pool.etfs:
            persisted = add_etf(
                session,
                exchange=etf.exchange,
                symbol=etf.symbol,
                currency=pool.currency,
                category=etf.category,
            )
            etf_ids[etf.symbol] = persisted.id
        for trade_date in sessions:
            session.add(TradingCalendar(trade_date=trade_date, source="test"))
        for symbol, rows in canonical_provider_prices(sessions).items():
            session.add_all(to_market_price(row, etf_id=etf_ids[symbol]) for row in rows[:-1])
        session.commit()

    monkeypatch.setattr(market_data_fetcher, "_today", lambda: sessions[-1])
    try:
        initialize_database(app, database_url=database_url)
        app.dependency_overrides[get_app_config] = lambda: app_config
        app.dependency_overrides[get_market_data_provider] = lambda: provider
        client = TestClient(app)

        initial_dashboard = client.get("/api/dashboard")
        fetch = client.post("/api/market-data/fetch?mode=incremental")
        generated_signal = client.post("/api/strategy-signals/generate")
        manual_detail = client.get(f"/api/strategy-signals/{generated_signal.json()['signal_id']}")
        latest_signal = client.get("/api/strategy-signals/latest")
        backtest_run = client.post(
            f"/api/backtests/run?startDate={sessions[65].isoformat()}&endDate={sessions[-1].isoformat()}"
        )
        backtest_detail = client.get(f"/api/backtests/{backtest_run.json()['run_id']}")
        latest_after_backtest = client.get("/api/strategy-signals/latest")
        refreshed_dashboard = client.get("/api/dashboard")
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert initial_dashboard.status_code == 200
    assert initial_dashboard.json()["market_data"]["latest_trade_date"] == sessions[-2].isoformat()

    assert fetch.status_code == 200
    assert fetch.json() == {
        "status": "success",
        "requested_etf_count": len(pool.etfs),
        "rows_fetched": len(pool.etfs),
        "rows_inserted": len(pool.etfs),
        "rows_updated": 0,
        "failed_symbols": [],
        "error_message": None,
    }
    assert provider.requests == [
        ("159915", sessions[-2], sessions[-1]),
        ("510300", sessions[-2], sessions[-1]),
        ("511010", sessions[-2], sessions[-1]),
    ]

    assert generated_signal.status_code == 200
    generated = generated_signal.json()
    assert generated["status"] == "success"
    assert generated["signal_date"] == sessions[-1].isoformat()
    assert [
        (position["symbol"], position["rank"], position["target_weight"])
        for position in generated["positions"]
    ] == [("510300", 1, "1")]

    assert manual_detail.status_code == 200
    assert manual_detail.json()["signal"]["source"] == "manual"
    assert latest_signal.status_code == 200
    assert latest_signal.json()["signal"]["signal_id"] == generated["signal_id"]

    assert backtest_run.status_code == 200
    run = backtest_run.json()
    assert run["status"] == "success"
    assert run["trading_day_count"] == len(sessions[65:])

    assert backtest_detail.status_code == 200
    detail = backtest_detail.json()
    assert detail["run"]["run_id"] == run["run_id"]
    assert detail["metrics"]["total_return"] == run["total_return"]
    assert len(detail["equity_curve"]) == run["trading_day_count"]
    assert detail["equity_curve"][-1]["trade_date"] == sessions[-1].isoformat()
    assert detail["signal_count"] == len(detail["signal_ids"]) == run["signal_count"]
    non_empty_positions = [
        json.loads(point["positions_json"])
        for point in detail["equity_curve"]
        if point["positions_json"] != "[]"
    ]
    assert non_empty_positions
    assert all(
        set(positions[0]) == {"etf_id", "target_weight", "actual_weight"}
        for positions in non_empty_positions
    )

    assert latest_after_backtest.status_code == 200
    latest_after = latest_after_backtest.json()
    assert latest_after["has_signal"] is True
    assert latest_after["signal"]["signal_id"] in detail["signal_ids"]

    assert refreshed_dashboard.status_code == 200
    dashboard = refreshed_dashboard.json()
    assert dashboard["market_data"]["latest_trade_date"] == sessions[-1].isoformat()
    assert dashboard["latest_signal"]["signal_id"] == latest_after["signal"]["signal_id"]
    assert dashboard["recent_backtest"]["run_id"] == run["run_id"]
    assert dashboard["recent_fetch_logs"][0]["mode"] == "incremental"
    assert dashboard["recent_fetch_logs"][0]["rows_inserted"] == len(pool.etfs)
