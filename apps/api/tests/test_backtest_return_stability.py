# ruff: noqa: E501

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.models import BacktestBenchmark, BacktestBenchmarkEquityCurve

from tests.integration_data import backtest_run, equity_curve_row, prepare_sqlite_database

_BENCHMARK_KEYS = ("equal_weight_monthly", "csi_300_buy_hold")


def _seed_run(
    session_factory,
    *,
    point_count: int = 3,
    with_benchmarks: bool = True,
    benchmark_point_count: int = 3,
    parameters_json: str = '{"risk_free_rate": 0.02}',
) -> int:
    with session_factory() as session:
        run = backtest_run(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
            finished_at=datetime(2026, 2, 1, 9, 5, tzinfo=UTC),
        )
        run.parameters_json = parameters_json
        session.add(run)
        session.flush()
        for index in range(point_count):
            session.add(
                equity_curve_row(
                    run_id=run.id,
                    trade_date=date(2026, 1, 2) + timedelta(days=index),
                    net_value=Decimal("1.000000") + Decimal(index) / Decimal(100),
                )
            )
        if with_benchmarks:
            for key in _BENCHMARK_KEYS:
                benchmark = BacktestBenchmark(
                    backtest_run_id=run.id,
                    benchmark_key=key,
                    display_name=key,
                    total_return=Decimal("0.100000"),
                    annualized_return=Decimal("0.120000"),
                    max_drawdown=Decimal("-0.050000"),
                    sharpe_ratio=Decimal("1.100000"),
                    volatility=Decimal("0.140000"),
                )
                session.add(benchmark)
                session.flush()
                for index in range(benchmark_point_count):
                    session.add(
                        BacktestBenchmarkEquityCurve(
                            benchmark_id=benchmark.id,
                            trade_date=date(2026, 1, 2) + timedelta(days=index),
                            net_value=Decimal("1.000000") + Decimal(index) / Decimal(200),
                        )
                    )
        session.commit()
        return run.id


def test_detail_returns_exact_core_derived_series_for_strategy_and_benchmarks(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'stability-detail.db'}"
    session_factory = prepare_sqlite_database(database_url)
    run_id = _seed_run(session_factory, point_count=3, benchmark_point_count=3)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get(f"/api/backtests/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    stability = response.json()["return_stability"]
    assert stability["strategy"]["window_sessions"] == 63
    assert stability["strategy"]["rolling_status"] == "insufficient_observations"
    assert stability["strategy"]["source_point_count"] == 3
    assert stability["strategy"]["effective_return_count"] == 2
    assert stability["strategy"]["rolling"] == []
    assert stability["strategy"]["monthly"][0]["period"] == "2026-01"
    assert stability["strategy"]["monthly"][0]["observation_count"] == 2
    assert stability["strategy"]["monthly"][0]["total_return"] == "0.020000"
    assert stability["strategy"]["monthly"][0]["is_partial"] is False
    assert [benchmark["key"] for benchmark in stability["benchmarks"]] == list(_BENCHMARK_KEYS)
    equal_weight = stability["benchmarks"][0]
    assert equal_weight["name"] == "equal_weight_monthly"
    assert equal_weight["source_point_count"] == 3
    assert equal_weight["monthly"][0]["total_return"] == "0.010000"


def test_detail_returns_rolling_series_for_sufficient_curve(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'stability-rolling.db'}"
    session_factory = prepare_sqlite_database(database_url)
    run_id = _seed_run(session_factory, point_count=65, benchmark_point_count=65)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get(f"/api/backtests/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    stability = response.json()["return_stability"]
    strategy = stability["strategy"]
    assert strategy["rolling_status"] == "available"
    assert strategy["sharpe_status"] == "available"
    assert len(strategy["rolling"]) == 2
    first = strategy["rolling"][0]
    assert first["window_start_date"] == "2026-01-02"
    assert first["trade_date"] == "2026-03-06"
    assert first["total_return"] == "0.630000"
    assert isinstance(first["volatility"], str)
    assert isinstance(first["sharpe_ratio"], str)
    assert first["sharpe_ratio"] is not None


def test_detail_returns_nullable_sharpe_without_risk_free_evidence(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'stability-no-rf.db'}"
    session_factory = prepare_sqlite_database(database_url)
    run_id = _seed_run(
        session_factory,
        point_count=65,
        with_benchmarks=False,
        parameters_json='{"top_n": 2}',
    )

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get(f"/api/backtests/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    stability = response.json()["return_stability"]
    strategy = stability["strategy"]
    assert strategy["rolling_status"] == "available"
    assert strategy["sharpe_status"] == "unavailable_missing_risk_free_rate"
    assert all(point["sharpe_ratio"] is None for point in strategy["rolling"])
    assert all(point["total_return"] is not None for point in strategy["rolling"])
    assert stability["benchmarks"] == []


def test_detail_keeps_empty_strategy_curve_explicit(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'stability-empty.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        run = backtest_run(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
            finished_at=datetime(2026, 2, 1, 9, 5, tzinfo=UTC),
        )
        run.parameters_json = '{"risk_free_rate": 0.02}'
        session.add(run)
        session.commit()
        run_id = run.id

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get(f"/api/backtests/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    strategy = response.json()["return_stability"]["strategy"]
    assert strategy["rolling_status"] == "insufficient_observations"
    assert strategy["source_point_count"] == 0
    assert strategy["effective_return_count"] == 0
    assert strategy["rolling"] == []
    assert strategy["monthly"] == []
    assert strategy["yearly"] == []


def test_detail_returns_error_envelope_for_corrupt_curve(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'stability-corrupt.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        run = backtest_run(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            started_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
            finished_at=datetime(2026, 2, 1, 9, 5, tzinfo=UTC),
        )
        run.parameters_json = '{"risk_free_rate": 0.02}'
        session.add(run)
        session.flush()
        # Non-positive persisted net value violates the stability contract.
        session.add(
            equity_curve_row(
                run_id=run.id,
                trade_date=date(2026, 1, 2),
                net_value=Decimal("1.000000"),
            )
        )
        session.add(
            equity_curve_row(
                run_id=run.id,
                trade_date=date(2026, 1, 3),
                net_value=Decimal("0.000000"),
            )
        )
        session.commit()
        run_id = run.id

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app, raise_server_exceptions=False).get(f"/api/backtests/{run_id}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "unexpected_error"


def test_list_payload_remains_unbounded(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'stability-list.db'}"
    session_factory = prepare_sqlite_database(database_url)
    _seed_run(session_factory, point_count=65)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/backtests")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert all("return_stability" not in run for run in response.json()["runs"])


def test_run_creation_payload_remains_unbounded(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'stability-run.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).post(
            "/api/backtests/run?startDate=2026-02-01&endDate=2026-02-02"
        )
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 400  # no market data -> no run created
    assert "return_stability" not in response.json()
