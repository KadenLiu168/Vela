from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.models import BacktestRun, StrategySignal, StrategySignalPosition

from tests.integration_data import add_etf, prepare_sqlite_database


def _seed_signals(session_factory) -> None:
    with session_factory() as session:
        spy = add_etf(session, symbol="SPY")
        shy = add_etf(session, symbol="SHY")
        session.add_all(
            [
                StrategySignal(
                    signal_date=date(2026, 6, 22),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    source="manual",
                    generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
                    status="success",
                    result="hold",
                    positions=[
                        StrategySignalPosition(
                            etf_id=spy.id,
                            rank=1,
                            score=Decimal("0.800000"),
                            target_weight=Decimal("1.000000"),
                        )
                    ],
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 23),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    source="manual",
                    generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                    status="success",
                    result="rebalance",
                    positions=[
                        StrategySignalPosition(
                            etf_id=shy.id,
                            rank=None,
                            score=None,
                            target_weight=Decimal("1.000000"),
                        )
                    ],
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 24),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    source="manual",
                    generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
                    status="failed",
                    result=None,
                    error_message="missing market data",
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 23),
                    strategy_id="Other_strategy",
                    config_version="v1",
                    source="manual",
                    generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                    status="success",
                    result="rebalance",
                    positions=[],
                ),
            ]
        )
        session.commit()


def test_list_strategy_signals_endpoint_returns_successful_signals_for_current_strategy(
    tmp_path,
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'signal-list.db'}"
    session_factory = prepare_sqlite_database(database_url)
    _seed_signals(session_factory)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/strategy-signals?limit=10&offset=0")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    signals = response.json()["signals"]
    assert [signal["signal_id"] for signal in signals] == [2, 1]
    assert signals[0]["result"] == "rebalance"
    assert signals[0]["position_count"] == 1
    assert signals[0]["is_fallback"] is True
    assert signals[0]["source"] == "manual"
    assert signals[0]["backtest_run_id"] is None
    assert signals[1]["position_count"] == 1
    assert signals[1]["is_fallback"] is False


def test_list_strategy_signals_endpoint_paginates_with_limit_and_offset(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'signal-list-page.db'}"
    session_factory = prepare_sqlite_database(database_url)
    _seed_signals(session_factory)

    try:
        initialize_database(app, database_url=database_url)

        page1 = TestClient(app).get("/api/strategy-signals?limit=1&offset=0").json()["signals"]
        page2 = TestClient(app).get("/api/strategy-signals?limit=1&offset=1").json()["signals"]
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert [signal["signal_id"] for signal in page1] == [2]
    assert [signal["signal_id"] for signal in page2] == [1]


def test_list_strategy_signals_endpoint_returns_empty_when_no_match(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'signal-list-empty.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/strategy-signals")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json() == {"signals": []}


def test_strategy_signal_detail_endpoint_returns_signal_by_id(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'signal-detail.db'}"
    session_factory = prepare_sqlite_database(database_url)
    _seed_signals(session_factory)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/strategy-signals/2")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["signal"] == {
        "signal_id": 2,
        "signal_date": "2026-06-23",
        "strategy_id": "Dual_momentum",
        "config_version": "v1",
        "generated_at": "2026-06-23T09:30:00",
        "result": "rebalance",
        "is_fallback": True,
        "source": "manual",
        "backtest_run_id": None,
    }
    assert body["positions"] == [
        {
            "exchange": "NYSEARCA",
            "symbol": "SHY",
            "name": "SHY ETF",
            "target_weight": "1.000000",
            "rank": None,
            "score": None,
            "is_fallback": True,
        }
    ]


def test_strategy_signal_detail_endpoint_returns_404_for_foreign_strategy(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'signal-foreign.db'}"
    session_factory = prepare_sqlite_database(database_url)
    _seed_signals(session_factory)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/strategy-signals/4")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 404


def test_strategy_signal_detail_endpoint_returns_current_strategy_across_versions(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'signal-historical.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        session.add(
            StrategySignal(
                signal_date=date(2026, 6, 23),
                strategy_id="Dual_momentum",
                config_version="wf-historical",
                source="backtest",
                generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                status="success",
                result="rebalance",
                positions=[],
            )
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)
        response = TestClient(app).get("/api/strategy-signals/1")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json()["signal"]["config_version"] == "wf-historical"


def test_strategy_signal_detail_endpoint_returns_404_for_unknown_id(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'signal-unknown.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/strategy-signals/999")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 404


def _seed_mixed_source_signals(session_factory) -> dict[str, int]:
    with session_factory() as session:
        spy = add_etf(session, symbol="SPY")
        run = BacktestRun(
            strategy_id="Dual_momentum",
            config_version="v1",
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
        session.add_all(
            [
                StrategySignal(
                    signal_date=date(2026, 6, 22),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    source="manual",
                    generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
                    status="success",
                    result="hold",
                    positions=[
                        StrategySignalPosition(
                            etf_id=spy.id,
                            rank=1,
                            score=Decimal("0.800000"),
                            target_weight=Decimal("1.000000"),
                        )
                    ],
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 23),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    source="manual",
                    generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                    status="success",
                    result="rebalance",
                    positions=[],
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 24),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    source="scheduled",
                    generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
                    status="success",
                    result="rebalance",
                    positions=[],
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 25),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    source="backtest",
                    backtest_run_id=run.id,
                    generated_at=datetime(2026, 6, 25, 9, 30, tzinfo=UTC),
                    status="success",
                    result="buy",
                    positions=[],
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 26),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    source="legacy",
                    generated_at=datetime(2026, 6, 26, 9, 30, tzinfo=UTC),
                    status="success",
                    result="empty",
                    positions=[],
                ),
            ]
        )
        session.commit()
        return {"backtest_run_id": run.id}


def test_list_strategy_signals_endpoint_filters_by_source(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'signal-source-filter.db'}"
    session_factory = prepare_sqlite_database(database_url)
    _seed_mixed_source_signals(session_factory)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/strategy-signals?source=backtest")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    signals = response.json()["signals"]
    assert [signal["signal_id"] for signal in signals] == [4]
    assert signals[0]["source"] == "backtest"
    assert signals[0]["backtest_run_id"] is not None


def test_list_strategy_signals_endpoint_accepts_every_declared_source(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'signal-source-enum.db'}"
    session_factory = prepare_sqlite_database(database_url)
    _seed_mixed_source_signals(session_factory)

    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)

        for source in StrategySignal.SOURCES:
            response = client.get(f"/api/strategy-signals?source={source}")
            assert response.status_code == 200
            signals = response.json()["signals"]
            assert signals, f"source {source} returned no signals"
            assert all(signal["source"] == source for signal in signals)
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)


def test_list_strategy_signals_endpoint_paginates_filtered_source(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'signal-source-page.db'}"
    session_factory = prepare_sqlite_database(database_url)
    _seed_mixed_source_signals(session_factory)

    try:
        initialize_database(app, database_url=database_url)
        client = TestClient(app)

        page1 = client.get("/api/strategy-signals?source=manual&limit=1&offset=0").json()["signals"]
        page2 = client.get("/api/strategy-signals?source=manual&limit=1&offset=1").json()["signals"]
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert [signal["signal_id"] for signal in page1] == [2]
    assert [signal["signal_id"] for signal in page2] == [1]


@pytest.mark.parametrize("invalid_source", ["unknown", "", "null"])
def test_list_strategy_signals_endpoint_rejects_invalid_source(
    tmp_path, invalid_source: str
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'signal-source-invalid.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get(f"/api/strategy-signals?source={invalid_source}")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "validation_error",
        "category": "validation",
        "message": "Request validation failed",
    }
