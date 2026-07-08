from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.models import StrategySignal, StrategySignalPosition

from tests.integration_data import add_etf, prepare_sqlite_database


def test_latest_strategy_signal_endpoint_reads_persisted_sqlite_rows(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'latest-signal.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        spy = add_etf(session, symbol="SPY")
        qqq = add_etf(session, symbol="QQQ")
        shy = add_etf(session, symbol="SHY")
        session.add_all(
            [
                StrategySignal(
                    signal_date=date(2026, 6, 22),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
                    status="success",
                    result="hold",
                    positions=[
                        StrategySignalPosition(
                            etf_id=qqq.id,
                            rank=1,
                            score=Decimal("0.700000"),
                            target_weight=Decimal("1.000000"),
                        )
                    ],
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 24),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    generated_at=datetime(2026, 6, 24, 9, 40, tzinfo=UTC),
                    status="failed",
                    result=None,
                    error_message="missing market data",
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 22),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    generated_at=datetime(2026, 6, 24, 9, 35, tzinfo=UTC),
                    status="success",
                    result="hold",
                    positions=[
                        StrategySignalPosition(
                            etf_id=qqq.id,
                            rank=1,
                            score=Decimal("0.700000"),
                            target_weight=Decimal("1.000000"),
                        )
                    ],
                ),
                StrategySignal(
                    signal_date=date(2026, 6, 23),
                    strategy_id="Dual_momentum",
                    config_version="v1",
                    generated_at=datetime(2026, 6, 24, 9, 35, tzinfo=UTC),
                    status="success",
                    result="rebalance",
                    positions=[
                        StrategySignalPosition(
                            etf_id=shy.id,
                            rank=None,
                            score=None,
                            target_weight=Decimal("0.500000"),
                        ),
                        StrategySignalPosition(
                            etf_id=spy.id,
                            rank=1,
                            score=Decimal("0.800000"),
                            target_weight=Decimal("0.500000"),
                        ),
                    ],
                ),
            ]
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/strategy-signals/latest")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["has_signal"] is True
    assert body["signal"] == {
        "signal_id": 4,
        "signal_date": "2026-06-23",
        "config_version": "v1",
        "generated_at": "2026-06-24T09:35:00",
        "result": "rebalance",
        "is_fallback": True,
    }
    assert body["positions"] == [
        {
            "exchange": "NYSEARCA",
            "symbol": "SPY",
            "target_weight": "0.500000",
            "rank": 1,
            "score": "0.800000",
            "is_fallback": False,
        },
        {
            "exchange": "NYSEARCA",
            "symbol": "SHY",
            "target_weight": "0.500000",
            "rank": None,
            "score": None,
            "is_fallback": True,
        },
    ]


def test_latest_strategy_signal_endpoint_returns_stable_empty_state(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'empty-latest-signal.db'}"
    session_factory = prepare_sqlite_database(database_url)
    with session_factory() as session:
        session.add(
            StrategySignal(
                signal_date=date(2026, 6, 24),
                strategy_id="Dual_momentum",
                config_version="v1",
                generated_at=datetime(2026, 6, 24, 9, 40, tzinfo=UTC),
                status="failed",
                result=None,
                error_message="missing market data",
            )
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).get("/api/strategy-signals/latest")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json() == {
        "has_signal": False,
        "signal": None,
        "positions": [],
    }
