from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL, create_engine_from_url, create_session_factory
from vela_core.models import Base, ETFInfo, MarketPrice, StrategySignal, StrategySignalPosition


def test_strategy_signal_generate_endpoint_uses_latest_local_market_date(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'generate-signal.db'}"
    session_factory = _create_database(database_url)
    latest_trade_date = date(2026, 6, 23)
    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SZSE", symbol="159915")
        _add_etf(session, exchange="SSE", symbol="511010")
        _add_price_history(session, etf_id=first.id, end_date=latest_trade_date)
        _add_price_history(
            session,
            etf_id=second.id,
            end_date=latest_trade_date,
            current_price=Decimal("170"),
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
    session_factory = _create_database(database_url)
    explicit_signal_date = date(2026, 6, 22)
    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SZSE", symbol="159915")
        _add_etf(session, exchange="SSE", symbol="511010")
        _add_price_history(session, etf_id=first.id, end_date=date(2026, 6, 23))
        _add_price_history(
            session,
            etf_id=second.id,
            end_date=date(2026, 6, 23),
            current_price=Decimal("170"),
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
    _create_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).post("/api/strategy-signals/generate")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 400
    assert response.json() == {"detail": "No local market prices found"}


def test_strategy_signal_generate_endpoint_rejects_invalid_signal_date(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'invalid-generate-signal.db'}"
    _create_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).post("/api/strategy-signals/generate?signalDate=2026/06/22")
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 422


def _create_database(database_url: str) -> sessionmaker[Session]:
    engine = create_engine_from_url(database_url)
    Base.metadata.create_all(engine)
    return create_session_factory(engine, expire_on_commit=False)


def _add_etf(session: Session, *, exchange: str, symbol: str) -> ETFInfo:
    etf = ETFInfo(
        exchange=exchange,
        symbol=symbol,
        name=f"{symbol} ETF",
        currency="CNY",
    )
    session.add(etf)
    session.flush()
    return etf


def _add_price_history(
    session: Session,
    *,
    etf_id: int,
    end_date: date,
    current_price: Decimal = Decimal("180"),
) -> None:
    start_date = end_date - timedelta(days=130)
    session.add_all(
        MarketPrice(
            etf_id=etf_id,
            trade_date=start_date + timedelta(days=offset),
            open_price=close_price,
            high_price=close_price,
            low_price=close_price,
            close_price=close_price,
            adjusted_close=None,
            volume=1000,
        )
        for offset in range(131)
        for close_price in [
            current_price if offset in {129, 130} else Decimal("100"),
        ]
    )
