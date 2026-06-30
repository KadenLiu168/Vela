from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL, create_engine_from_url, create_session_factory
from vela_core.models import (
    BacktestRun,
    Base,
    ETFInfo,
    MarketPrice,
    StrategySignal,
    StrategySignalPosition,
)


def test_dashboard_endpoint_reads_persisted_sqlite_rows(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'dashboard.db'}"
    session_factory = _create_database(database_url)
    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        session.add_all(
            [
                _market_price(spy.id, trade_date=date(2026, 6, 22)),
                _market_price(qqq.id, trade_date=date(2026, 6, 23)),
                StrategySignal(
                    signal_date=date(2026, 6, 23),
                    config_version="v1",
                    generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                    status="success",
                    result="rebalance",
                    positions=[
                        StrategySignalPosition(
                            etf_id=spy.id,
                            rank=1,
                            score=Decimal("0.800000"),
                            target_weight=Decimal("0.500000"),
                        )
                    ],
                ),
                BacktestRun(
                    strategy_name="dual_momentum",
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
    }
    assert body["latest_signal"] == {
        "signal_id": 1,
        "signal_date": "2026-06-23",
        "config_version": "v1",
        "status": "success",
        "result": "rebalance",
        "generated_at": "2026-06-23T09:30:00",
        "position_count": 1,
    }
    assert body["recent_backtest"]["run_id"] == 1
    assert body["recent_backtest"]["total_return"] == "0.120000"
    assert body["recent_backtest"]["max_drawdown"] == "-0.050000"
    assert body["recent_backtest"]["sharpe_ratio"] == "1.100000"


def _create_database(database_url: str) -> sessionmaker[Session]:
    engine = create_engine_from_url(database_url)
    Base.metadata.create_all(engine)
    return create_session_factory(engine, expire_on_commit=False)


def _add_etf(session: Session, symbol: str) -> ETFInfo:
    etf = ETFInfo(
        exchange="NYSEARCA",
        symbol=symbol,
        name=f"{symbol} ETF",
        currency="USD",
    )
    session.add(etf)
    session.flush()
    return etf


def _market_price(etf_id: int, *, trade_date: date) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=Decimal("100.000000"),
        high_price=Decimal("101.000000"),
        low_price=Decimal("99.000000"),
        close_price=Decimal("100.000000"),
        adjusted_close=None,
        volume=1000,
    )
