from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.models import BacktestEquityCurve, BacktestRun, MarketPrice, StrategySignal

from tests.integration_data import (
    add_etf,
    backtest_run,
    equity_curve_row,
    prepare_sqlite_database,
)


def test_run_backtest_endpoint_runs_core_workflow_and_persists_results(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'run-backtest.db'}"
    session_factory = prepare_sqlite_database(database_url)
    start_date = date(2026, 1, 1)
    end_date = date(2026, 1, 10)
    with session_factory() as session:
        first = add_etf(session, exchange="SSE", symbol="510300", currency="CNY")
        second = add_etf(session, exchange="SZSE", symbol="159915", currency="CNY")
        defense = add_etf(session, exchange="SSE", symbol="511010", currency="CNY")
        defense_second = add_etf(session, exchange="SSE", symbol="511880", currency="CNY")
        defense_third = add_etf(session, exchange="SSE", symbol="518880", currency="CNY")
        _add_price_history(session, etf_id=first.id, start_date=start_date, end_date=end_date)
        _add_price_history(
            session,
            etf_id=second.id,
            start_date=start_date,
            end_date=end_date,
            daily_step=Decimal("0.08"),
        )
        _add_price_history(
            session,
            etf_id=defense.id,
            start_date=start_date,
            end_date=end_date,
            daily_step=Decimal("0.01"),
        )
        _add_price_history(
            session,
            etf_id=defense_second.id,
            start_date=start_date,
            end_date=end_date,
            daily_step=Decimal("0.01"),
        )
        _add_price_history(
            session,
            etf_id=defense_third.id,
            start_date=start_date,
            end_date=end_date,
            daily_step=Decimal("0.01"),
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).post(
            "/api/backtests/run?startDate=2026-01-01&endDate=2026-01-10"
        )
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == 1
    assert body["status"] == "success"
    assert body["start_date"] == "2026-01-01"
    assert body["end_date"] == "2026-01-10"
    assert body["trading_day_count"] == 10
    assert body["signal_count"] == 2
    assert body["total_return"] is not None
    assert body["annualized_return"] is not None
    assert body["max_drawdown"] == "-0.000500"
    assert body["volatility"] is not None
    assert body["sharpe_ratio"] is not None

    with session_factory() as session:
        run = session.query(BacktestRun).one()
        curve_rows = (
            session.query(BacktestEquityCurve).order_by(BacktestEquityCurve.trade_date).all()
        )

    assert run.id == body["run_id"]
    assert run.start_date == start_date
    assert run.end_date == end_date
    assert run.status == "success"
    assert len(curve_rows) == body["trading_day_count"]
    assert curve_rows[0].backtest_run_id == run.id


def test_run_backtest_endpoint_updates_backtest_detail(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'run-backtest-detail-loop.db'}"
    session_factory = prepare_sqlite_database(database_url)
    start_date = date(2026, 1, 1)
    end_date = date(2026, 1, 10)
    with session_factory() as session:
        first = add_etf(session, exchange="SSE", symbol="510300", currency="CNY")
        second = add_etf(session, exchange="SZSE", symbol="159915", currency="CNY")
        defense = add_etf(session, exchange="SSE", symbol="511010", currency="CNY")
        defense_second = add_etf(session, exchange="SSE", symbol="511880", currency="CNY")
        defense_third = add_etf(session, exchange="SSE", symbol="518880", currency="CNY")
        _add_price_history(session, etf_id=first.id, start_date=start_date, end_date=end_date)
        _add_price_history(
            session,
            etf_id=second.id,
            start_date=start_date,
            end_date=end_date,
            daily_step=Decimal("0.08"),
        )
        _add_price_history(
            session,
            etf_id=defense.id,
            start_date=start_date,
            end_date=end_date,
            daily_step=Decimal("0.01"),
        )
        _add_price_history(
            session,
            etf_id=defense_second.id,
            start_date=start_date,
            end_date=end_date,
            daily_step=Decimal("0.01"),
        )
        _add_price_history(
            session,
            etf_id=defense_third.id,
            start_date=start_date,
            end_date=end_date,
            daily_step=Decimal("0.01"),
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)

        run_response = client.post("/api/backtests/run?startDate=2026-01-01&endDate=2026-01-10")
        detail_response = client.get(f"/api/backtests/{run_response.json()['run_id']}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert run_response.status_code == 200
    run_body = run_response.json()
    assert run_body["run_id"] == 1
    assert run_body["status"] == "success"
    assert run_body["trading_day_count"] == 10
    assert run_body["signal_count"] == 2
    assert run_body["total_return"] is not None

    with session_factory() as session:
        run = session.query(BacktestRun).one()
        signals = session.query(StrategySignal).order_by(StrategySignal.signal_date).all()
        curve_rows = (
            session.query(BacktestEquityCurve).order_by(BacktestEquityCurve.trade_date).all()
        )

    assert run.id == run_body["run_id"]
    assert run.status == "success"
    assert [signal.status for signal in signals] == ["success", "success"]
    assert [signal.source for signal in signals] == ["backtest", "backtest"]
    assert [signal.backtest_run_id for signal in signals] == [run.id, run.id]
    assert len(curve_rows) == run_body["trading_day_count"]

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["run"]["run_id"] == run_body["run_id"]
    assert detail["run"]["start_date"] == run_body["start_date"]
    assert detail["run"]["end_date"] == run_body["end_date"]
    assert detail["run"]["status"] == run_body["status"]
    assert detail["metrics"] == {
        "total_return": run_body["total_return"],
        "annualized_return": run_body["annualized_return"],
        "max_drawdown": run_body["max_drawdown"],
        "volatility": run_body["volatility"],
        "sharpe_ratio": run_body["sharpe_ratio"],
    }
    assert len(detail["equity_curve"]) == len(curve_rows)
    assert detail["equity_curve"][0]["trade_date"] == curve_rows[0].trade_date.isoformat()
    assert detail["equity_curve"][-1]["trade_date"] == curve_rows[-1].trade_date.isoformat()
    assert detail["equity_curve"][-1]["net_value"] == str(curve_rows[-1].net_value)
    assert detail["signal_ids"] == [signal.id for signal in signals]
    assert detail["signal_count"] == len(signals)


def test_run_backtest_endpoint_rejects_invalid_date_range(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'invalid-range.db'}"
    session_factory = prepare_sqlite_database(database_url)

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
    with session_factory() as session:
        assert session.query(BacktestRun).count() == 0


def test_run_backtest_endpoint_requires_date_query_params(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'missing-date.db'}"

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).post("/api/backtests/run")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 422


def test_list_backtests_endpoint_reads_recent_persisted_runs(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'list-backtests.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        session.add_all(
            [
                backtest_run(
                    start_date=date(2026, 1, 1),
                    end_date=date(2026, 1, 31),
                    started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
                    finished_at=datetime(2026, 2, 1, 9, 5, tzinfo=UTC),
                    total_return=Decimal("0.120000"),
                ),
                backtest_run(
                    start_date=date(2026, 2, 1),
                    end_date=date(2026, 2, 28),
                    started_at=datetime(2026, 3, 1, 9, 0, tzinfo=UTC),
                    finished_at=None,
                    status="running",
                    total_return=None,
                ),
                backtest_run(
                    start_date=date(2026, 3, 1),
                    end_date=date(2026, 3, 31),
                    started_at=datetime(2026, 3, 1, 9, 0, tzinfo=UTC),
                    finished_at=datetime(2026, 3, 1, 9, 4, tzinfo=UTC),
                    total_return=Decimal("0.050000"),
                ),
            ]
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/backtests")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json() == {
        "runs": [
            {
                "run_id": 3,
                "strategy_id": "Dual_momentum",
                "config_version": "v1",
                "start_date": "2026-03-01",
                "end_date": "2026-03-31",
                "status": "success",
                "started_at": "2026-03-01T09:00:00",
                "finished_at": "2026-03-01T09:04:00",
                "total_return": "0.050000",
                "annualized_return": "0.180000",
                "max_drawdown": "-0.050000",
                "volatility": "0.200000",
                "sharpe_ratio": "1.100000",
            },
            {
                "run_id": 2,
                "strategy_id": "Dual_momentum",
                "config_version": "v1",
                "start_date": "2026-02-01",
                "end_date": "2026-02-28",
                "status": "running",
                "started_at": "2026-03-01T09:00:00",
                "finished_at": None,
                "total_return": None,
                "annualized_return": "0.180000",
                "max_drawdown": "-0.050000",
                "volatility": "0.200000",
                "sharpe_ratio": "1.100000",
            },
            {
                "run_id": 1,
                "strategy_id": "Dual_momentum",
                "config_version": "v1",
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "status": "success",
                "started_at": "2026-02-01T09:00:00",
                "finished_at": "2026-02-01T09:05:00",
                "total_return": "0.120000",
                "annualized_return": "0.180000",
                "max_drawdown": "-0.050000",
                "volatility": "0.200000",
                "sharpe_ratio": "1.100000",
            },
        ]
    }


def test_list_backtests_endpoint_supports_limit(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'list-backtests-limit.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        session.add_all(
            [
                backtest_run(
                    start_date=date(2026, 1, 1),
                    end_date=date(2026, 1, 31),
                    started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
                ),
                backtest_run(
                    start_date=date(2026, 2, 1),
                    end_date=date(2026, 2, 28),
                    started_at=datetime(2026, 3, 1, 9, 0, tzinfo=UTC),
                ),
            ]
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/backtests?limit=1")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert [run["run_id"] for run in response.json()["runs"]] == [2]


def test_list_backtests_endpoint_supports_offset(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'list-backtests-offset.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        session.add_all(
            [
                backtest_run(
                    start_date=date(2026, 1, 1),
                    end_date=date(2026, 1, 31),
                    started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
                ),
                backtest_run(
                    start_date=date(2026, 2, 1),
                    end_date=date(2026, 2, 28),
                    started_at=datetime(2026, 3, 1, 9, 0, tzinfo=UTC),
                ),
            ]
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/backtests?limit=10&offset=1")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert [run["run_id"] for run in response.json()["runs"]] == [1]


def test_list_backtests_endpoint_returns_empty_list(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'empty-list-backtests.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/backtests")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json() == {"runs": []}


def test_backtest_detail_endpoint_reads_persisted_run_and_ordered_curve(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'backtest-detail.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        run = backtest_run(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
            finished_at=datetime(2026, 2, 1, 9, 5, tzinfo=UTC),
            total_return=Decimal("0.120000"),
        )
        session.add(run)
        session.flush()
        session.add_all(
            [
                equity_curve_row(
                    run_id=run.id,
                    trade_date=date(2026, 1, 3),
                    net_value=Decimal("1.030000"),
                ),
                equity_curve_row(
                    run_id=run.id,
                    trade_date=date(2026, 1, 2),
                    net_value=Decimal("1.010000"),
                ),
            ]
        )
        session.commit()
        run_id = run.id

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get(f"/api/backtests/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json() == {
        "run": {
            "run_id": run_id,
            "strategy_id": "Dual_momentum",
            "config_version": "v1",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "parameters_json": '{"top_n": 2}',
            "status": "success",
            "error_message": None,
            "started_at": "2026-02-01T09:00:00",
            "finished_at": "2026-02-01T09:05:00",
        },
        "metrics": {
            "total_return": "0.120000",
            "annualized_return": "0.180000",
            "max_drawdown": "-0.050000",
            "volatility": "0.200000",
            "sharpe_ratio": "1.100000",
        },
        "equity_curve": [
            {
                "trade_date": "2026-01-02",
                "net_value": "1.010000",
                "cash": "100.000000",
                "market_value": "9900.000000",
                "total_assets": "10000.000000",
                "positions_json": '[{"symbol": "510300", "weight": 1.0}]',
            },
            {
                "trade_date": "2026-01-03",
                "net_value": "1.030000",
                "cash": "100.000000",
                "market_value": "9900.000000",
                "total_assets": "10000.000000",
                "positions_json": '[{"symbol": "510300", "weight": 1.0}]',
            },
        ],
        "signal_ids": [],
        "signal_count": 0,
    }


def test_backtest_detail_endpoint_returns_stable_not_found(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'missing-backtest-detail.db'}"
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


def test_backtest_detail_endpoint_returns_404_for_foreign_strategy(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'foreign-backtest-detail.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        session.add(
            BacktestRun(
                strategy_id="Other_strategy",
                config_version="v1",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 31),
                parameters_json='{"top_n": 2}',
                started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
                finished_at=datetime(2026, 2, 1, 9, 5, tzinfo=UTC),
                status="success",
                error_message=None,
                total_return=Decimal("0.120000"),
                annualized_return=Decimal("0.180000"),
                max_drawdown=Decimal("-0.050000"),
                volatility=Decimal("0.200000"),
                sharpe_ratio=Decimal("1.100000"),
            )
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/backtests/1")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 404


def _add_price_history(
    session: Session,
    *,
    etf_id: int,
    start_date: date,
    end_date: date,
    daily_step: Decimal = Decimal("0.10"),
) -> None:
    first_history_date = start_date - timedelta(days=130)
    total_days = (end_date - first_history_date).days
    session.add_all(
        MarketPrice(
            etf_id=etf_id,
            trade_date=first_history_date + timedelta(days=offset),
            open_price=close_price,
            high_price=close_price,
            low_price=close_price,
            close_price=close_price,
            factor_hfq=Decimal("1"),
            volume=1000,
        )
        for offset in range(total_days + 1)
        for close_price in [Decimal("100.000000") + daily_step * Decimal(offset)]
    )


def _seed_backtest_run_with_signals(
    session_factory,
    *,
    signal_dates: list[date],
    strategy_id: str = "Dual_momentum",
    config_version: str = "v1",
) -> int:
    with session_factory() as session:
        run = BacktestRun(
            strategy_id=strategy_id,
            config_version=config_version,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            parameters_json='{"top_n": 2}',
            started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
            finished_at=datetime(2026, 2, 1, 9, 5, tzinfo=UTC),
            status="success",
            total_return=Decimal("0.120000"),
            annualized_return=Decimal("0.180000"),
            max_drawdown=Decimal("-0.050000"),
            volatility=Decimal("0.200000"),
            sharpe_ratio=Decimal("1.100000"),
        )
        session.add(run)
        session.flush()
        for signal_date in signal_dates:
            session.add(
                StrategySignal(
                    signal_date=signal_date,
                    strategy_id=strategy_id,
                    config_version=config_version,
                    source="backtest",
                    backtest_run_id=run.id,
                    generated_at=datetime(
                        signal_date.year, signal_date.month, signal_date.day, 9, 30, tzinfo=UTC
                    ),
                    status="success",
                    result="rebalance",
                )
            )
        session.commit()
        return run.id


def test_backtest_signals_endpoint_returns_paginated_summaries(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'backtest-signals.db'}"
    session_factory = prepare_sqlite_database(database_url)
    run_id = _seed_backtest_run_with_signals(
        session_factory,
        signal_dates=[date(2026, 6, 3), date(2026, 6, 1), date(2026, 6, 2)],
    )

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get(f"/api/backtests/{run_id}/signals?limit=20&offset=0")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert list(body.keys()) == ["signals"]
    signals = body["signals"]
    assert [signal["signal_date"] for signal in signals] == [
        "2026-06-01",
        "2026-06-02",
        "2026-06-03",
    ]
    for signal in signals:
        assert set(signal.keys()) == {
            "signal_id",
            "signal_date",
            "result",
            "backtest_run_id",
        }
        assert signal["result"] == "rebalance"
        assert signal["backtest_run_id"] == run_id


def test_backtest_signals_endpoint_uses_default_pagination(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'backtest-signals-default.db'}"
    session_factory = prepare_sqlite_database(database_url)
    run_id = _seed_backtest_run_with_signals(
        session_factory,
        signal_dates=[date(2026, 6, 1), date(2026, 6, 2)],
    )

    try:
        initialize_database(app, database_url=database_url)

        default_response = TestClient(app).get(f"/api/backtests/{run_id}/signals")
        explicit_response = TestClient(app).get(
            f"/api/backtests/{run_id}/signals?limit=20&offset=0"
        )
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert default_response.status_code == 200
    assert default_response.json() == explicit_response.json()
    assert [signal["signal_date"] for signal in default_response.json()["signals"]] == [
        "2026-06-01",
        "2026-06-02",
    ]


def test_backtest_signals_endpoint_honors_offset(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'backtest-signals-offset.db'}"
    session_factory = prepare_sqlite_database(database_url)
    run_id = _seed_backtest_run_with_signals(
        session_factory,
        signal_dates=[date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)],
    )

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get(f"/api/backtests/{run_id}/signals?limit=20&offset=1")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert [signal["signal_date"] for signal in response.json()["signals"]] == [
        "2026-06-02",
        "2026-06-03",
    ]


def test_backtest_signals_endpoint_returns_empty_when_no_signals(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'backtest-signals-empty.db'}"
    session_factory = prepare_sqlite_database(database_url)
    run_id = _seed_backtest_run_with_signals(session_factory, signal_dates=[])

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get(f"/api/backtests/{run_id}/signals")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json() == {"signals": []}


def test_backtest_signals_endpoint_returns_404_for_unknown_run(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'backtest-signals-unknown.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/backtests/999/signals")
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


def test_backtest_signals_endpoint_returns_404_for_foreign_strategy(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'backtest-signals-foreign-strategy.db'}"
    session_factory = prepare_sqlite_database(database_url)
    foreign_run_id = _seed_backtest_run_with_signals(
        session_factory,
        signal_dates=[date(2026, 6, 1)],
        strategy_id="Other_strategy",
        config_version="v1",
    )

    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)

        foreign_response = client.get(f"/api/backtests/{foreign_run_id}/signals")
        unknown_response = client.get("/api/backtests/999/signals")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert foreign_response.status_code == 404
    assert unknown_response.status_code == 404
    assert foreign_response.json() == unknown_response.json()


def test_backtest_signals_endpoint_returns_404_for_foreign_config(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'backtest-signals-foreign-config.db'}"
    session_factory = prepare_sqlite_database(database_url)
    foreign_run_id = _seed_backtest_run_with_signals(
        session_factory,
        signal_dates=[date(2026, 6, 1)],
        strategy_id="Dual_momentum",
        config_version="v2",
    )

    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)

        foreign_response = client.get(f"/api/backtests/{foreign_run_id}/signals")
        unknown_response = client.get("/api/backtests/999/signals")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert foreign_response.status_code == 404
    assert unknown_response.status_code == 404
    assert foreign_response.json() == unknown_response.json()


@pytest.mark.parametrize("query_string", ["limit=0", "limit=101", "offset=-1"])
def test_backtest_signals_endpoint_rejects_invalid_pagination(tmp_path, query_string: str) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'backtest-signals-invalid.db'}"
    session_factory = prepare_sqlite_database(database_url)
    run_id = _seed_backtest_run_with_signals(session_factory, signal_dates=[date(2026, 6, 1)])

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get(f"/api/backtests/{run_id}/signals?{query_string}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "validation_error",
        "category": "validation",
        "message": "Request validation failed",
    }


def test_backtest_signals_endpoint_collection_matches_signal_count(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'backtest-signals-collection.db'}"
    session_factory = prepare_sqlite_database(database_url)
    signal_dates = [date(2026, 6, 1) + timedelta(days=day) for day in range(25)]
    run_id = _seed_backtest_run_with_signals(session_factory, signal_dates=signal_dates)

    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)

        detail = client.get(f"/api/backtests/{run_id}").json()
        collected_ids: list[int] = []
        offset = 0
        while True:
            page = client.get(f"/api/backtests/{run_id}/signals?limit=20&offset={offset}").json()[
                "signals"
            ]
            if not page:
                break
            collected_ids.extend(signal["signal_id"] for signal in page)
            offset += 20

        detail_signal_ids = set(detail["signal_ids"])
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert len(collected_ids) == detail["signal_count"]
    assert len(set(collected_ids)) == len(collected_ids)
    assert set(collected_ids) == detail_signal_ids
