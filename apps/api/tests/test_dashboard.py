from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.models import BacktestRun, StrategySignal, StrategySignalPosition

from tests.integration_data import (
    add_etf,
    data_fetch_log,
    market_price,
    prepare_sqlite_database,
)


def test_dashboard_endpoint_reads_persisted_sqlite_rows(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'dashboard.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        spy = add_etf(session, symbol="SPY")
        qqq = add_etf(session, symbol="QQQ")
        session.add_all(
            [
                market_price(etf_id=spy.id, trade_date=date(2026, 6, 22)),
                market_price(etf_id=qqq.id, trade_date=date(2026, 6, 23)),
                StrategySignal(
                    signal_date=date(2026, 6, 24),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
                    status="failed",
                    result=None,
                    error_message="No active ETFs found",
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 23),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                    status="success",
                    result="rebalance",
                    positions=[
                        StrategySignalPosition(
                            etf_id=spy.id,
                            rank=None,
                            score=None,
                            target_weight=Decimal("1.000000"),
                        )
                    ],
                ),
                BacktestRun(
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    start_date=date(2026, 1, 1),
                    end_date=date(2026, 1, 31),
                    parameters_json='{"top_n": 2}',
                    started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
                    finished_at=datetime(2026, 2, 1, 9, 1, tzinfo=UTC),
                    status="success",
                    total_return=Decimal("0.120000"),
                    max_drawdown=Decimal("-0.050000"),
                    sharpe_ratio=Decimal("1.100000"),
                ),
                data_fetch_log(
                    fetch_mode="incremental",
                    status="failed",
                    started_at=datetime(2026, 6, 24, 7, 59, tzinfo=UTC),
                    finished_at=datetime(2026, 6, 24, 8, 0, tzinfo=UTC),
                    rows_fetched=0,
                    rows_inserted=0,
                    rows_updated=0,
                    error_message="provider unavailable",
                ),
                data_fetch_log(
                    fetch_mode="full",
                    status="success",
                    started_at=datetime(2026, 6, 23, 7, 0, tzinfo=UTC),
                    finished_at=datetime(2026, 6, 23, 7, 5, tzinfo=UTC),
                    rows_fetched=200,
                    rows_inserted=180,
                    rows_updated=20,
                    error_message=None,
                ),
            ]
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/dashboard")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["strategy"]["strategy_id"] == "dual_momentum"
    assert body["strategy"]["version"] == "v1"
    assert body["market_data"] == {
        "price_rows": 2,
        "covered_etfs": 2,
        "earliest_trade_date": "2026-06-22",
        "latest_trade_date": "2026-06-23",
        "etf_list": [
            {"exchange": "NYSEARCA", "symbol": "QQQ", "name": "QQQ ETF", "category": None},
            {"exchange": "NYSEARCA", "symbol": "SPY", "name": "SPY ETF", "category": None},
        ],
    }
    assert body["latest_signal"] == {
        "signal_id": 2,
        "signal_date": "2026-06-23",
        "config_version": "v1",
        "status": "success",
        "result": "rebalance",
        "generated_at": "2026-06-23T09:30:00",
        "is_fallback": True,
        "position_count": 1,
    }
    assert body["recent_backtest"]["run_id"] == 1
    assert body["recent_backtest"]["start_date"] == "2026-01-01"
    assert body["recent_backtest"]["end_date"] == "2026-01-31"
    assert body["recent_backtest"]["status"] == "success"
    assert body["recent_backtest"]["total_return"] == "0.120000"
    assert body["recent_backtest"]["max_drawdown"] == "-0.050000"
    assert body["recent_backtest"]["sharpe_ratio"] == "1.100000"
    assert body["recent_fetch_logs"] == [
        {
            "fetch_log_id": 1,
            "fetch_time": "2026-06-24T08:00:00",
            "mode": "incremental",
            "status": "failed",
            "rows_fetched": 0,
            "rows_inserted": 0,
            "rows_updated": 0,
            "error_summary": "provider unavailable",
        },
        {
            "fetch_log_id": 2,
            "fetch_time": "2026-06-23T07:05:00",
            "mode": "full",
            "status": "success",
            "rows_fetched": 200,
            "rows_inserted": 180,
            "rows_updated": 20,
            "error_summary": None,
        },
    ]


def test_dashboard_endpoint_returns_empty_workflow_data_from_empty_sqlite(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'empty-dashboard.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/dashboard")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["market_data"] == {
        "price_rows": 0,
        "covered_etfs": 0,
        "earliest_trade_date": None,
        "latest_trade_date": None,
        "etf_list": [],
    }
    assert body["latest_signal"] is None
    assert body["recent_backtest"] is None
    assert body["recent_fetch_logs"] == []
