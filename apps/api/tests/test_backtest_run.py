from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from vela_api.database import initialize_database
from vela_api.main import app
from vela_core.database import DEFAULT_DATABASE_URL, create_engine_from_url, create_session_factory
from vela_core.models import BacktestEquityCurve, BacktestRun, Base, ETFInfo, MarketPrice


def test_run_backtest_endpoint_runs_core_workflow_and_persists_results(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'run-backtest.db'}"
    session_factory = _create_database(database_url)
    start_date = date(2026, 1, 1)
    end_date = date(2026, 1, 10)
    with session_factory() as session:
        first = _add_etf(session, exchange="SSE", symbol="510300")
        second = _add_etf(session, exchange="SZSE", symbol="159915")
        defense = _add_etf(session, exchange="SSE", symbol="511010")
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
    assert body["max_drawdown"] == "0.000000"
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


def test_run_backtest_endpoint_rejects_invalid_date_range(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'invalid-range.db'}"
    session_factory = _create_database(database_url)

    try:
        initialize_database(app, database_url=database_url)

        response = TestClient(app).post(
            "/api/backtests/run?startDate=2026-01-10&endDate=2026-01-01"
        )
    finally:
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 400
    assert response.json() == {"detail": "start_date must be on or before end_date"}
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
            adjusted_close=None,
            volume=1000,
        )
        for offset in range(total_days + 1)
        for close_price in [Decimal("100.000000") + daily_step * Decimal(offset)]
    )
