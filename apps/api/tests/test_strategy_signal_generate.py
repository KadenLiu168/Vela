from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL
from vela_core.models import StrategySignal, StrategySignalPosition

from tests.integration_data import add_etf, add_price_history, prepare_sqlite_database


def test_strategy_signal_generate_endpoint_uses_latest_local_market_date(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'generate-signal.db'}"
    session_factory = prepare_sqlite_database(database_url)
    latest_trade_date = date(2026, 6, 23)
    with session_factory() as session:
        first = add_etf(session, exchange="SSE", symbol="510300", currency="CNY")
        second = add_etf(session, exchange="SZSE", symbol="159915", currency="CNY")
        add_etf(session, exchange="SSE", symbol="511010", currency="CNY")
        add_price_history(session, etf_id=first.id, end_date=latest_trade_date)
        add_price_history(
            session,
            etf_id=second.id,
            end_date=latest_trade_date,
            current_price=Decimal("170.000000"),
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).post("/api/strategy-signals/generate")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["signal_id"] == 1
    assert body["signal_date"] == "2026-06-23"
    assert body["config_version"] == "v1"
    assert body["status"] == "success"
    assert body["result"] == "rebalance"
    assert body["error_message"] is None
    assert [position["symbol"] for position in body["positions"]] == ["510300", "159915"]

    with session_factory() as session:
        signal = session.scalar(select(StrategySignal))
        positions = session.scalars(select(StrategySignalPosition)).all()

    assert signal is not None
    assert signal.signal_date == latest_trade_date
    assert signal.status == "success"
    assert len(positions) == 2


def test_strategy_signal_generate_endpoint_accepts_explicit_signal_date(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'generate-explicit-signal.db'}"
    session_factory = prepare_sqlite_database(database_url)
    explicit_signal_date = date(2026, 6, 22)
    with session_factory() as session:
        first = add_etf(session, exchange="SSE", symbol="510300", currency="CNY")
        second = add_etf(session, exchange="SZSE", symbol="159915", currency="CNY")
        add_etf(session, exchange="SSE", symbol="511010", currency="CNY")
        add_price_history(session, etf_id=first.id, end_date=date(2026, 6, 23))
        add_price_history(
            session,
            etf_id=second.id,
            end_date=date(2026, 6, 23),
            current_price=Decimal("170.000000"),
        )
        session.commit()

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).post("/api/strategy-signals/generate?signalDate=2026-06-22")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["signal_date"] == explicit_signal_date.isoformat()
    assert body["status"] == "success"

    with session_factory() as session:
        signal = session.scalar(select(StrategySignal))

    assert signal is not None
    assert signal.signal_date == explicit_signal_date


def test_strategy_signal_generate_endpoint_rejects_missing_local_market_date(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'empty-generate-signal.db'}"
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


def test_strategy_signal_generate_endpoint_rejects_invalid_signal_date(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'invalid-generate-signal.db'}"
    prepare_sqlite_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).post("/api/strategy-signals/generate?signalDate=2026/06/22")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 422
