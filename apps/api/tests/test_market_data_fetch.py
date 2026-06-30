from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from vela_api.database import initialize_database
from vela_api.main import app, get_market_data_provider
from vela_core import DailyPrice
from vela_core.database import DEFAULT_DATABASE_URL, create_engine_from_url, create_session_factory
from vela_core.models import Base, DataFetchLog, ETFInfo, MarketPrice


def test_market_data_fetch_endpoint_runs_incremental_workflow_with_sqlite(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'market-data.db'}"
    session_factory = _create_database(database_url)
    provider = ControlledMarketDataProvider(
        {"SPY": [_daily_price(symbol="SPY", trade_date=date(2026, 6, 18))]}
    )
    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_market_price(session, etf_id=spy.id, trade_date=date(2026, 6, 17))
        session.commit()

    try:
        initialize_database(app, database_url=database_url)
        app.dependency_overrides[get_market_data_provider] = lambda: provider

        response = TestClient(app).post("/api/market-data/fetch?mode=incremental")
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "requested_etf_count": 1,
        "rows_fetched": 1,
        "rows_inserted": 1,
        "rows_updated": 0,
        "failed_symbols": [],
        "error_message": None,
    }
    assert provider.requests == [("SPY", date(2026, 6, 18))]

    with session_factory() as session:
        prices = session.query(MarketPrice).order_by(MarketPrice.trade_date).all()
        log = session.query(DataFetchLog).one()

    assert [price.trade_date for price in prices] == [date(2026, 6, 17), date(2026, 6, 18)]
    assert log.fetch_mode == "incremental"
    assert log.status == "success"
    assert log.rows_fetched == 1
    assert log.rows_inserted == 1
    assert log.rows_updated == 0


def test_market_data_fetch_endpoint_runs_full_workflow(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'full-market-data.db'}"
    session_factory = _create_database(database_url)
    provider = ControlledMarketDataProvider(
        {"SPY": [_daily_price(symbol="SPY", trade_date=date(2026, 6, 18))]}
    )
    with session_factory() as session:
        _add_etf(session, symbol="SPY")
        session.commit()

    try:
        initialize_database(app, database_url=database_url)
        app.dependency_overrides[get_market_data_provider] = lambda: provider

        response = TestClient(app).post("/api/market-data/fetch?mode=full")
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "requested_etf_count": 1,
        "rows_fetched": 1,
        "rows_inserted": 1,
        "rows_updated": 0,
        "failed_symbols": [],
        "error_message": None,
    }
    assert provider.requests == [("SPY", None)]


def test_market_data_fetch_endpoint_rejects_invalid_mode(tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'invalid-market-data.db'}"
    provider = ControlledMarketDataProvider({})

    try:
        initialize_database(app, database_url=database_url)
        app.dependency_overrides[get_market_data_provider] = lambda: provider

        response = TestClient(app).post("/api/market-data/fetch?mode=recent")
    finally:
        app.dependency_overrides.clear()
        initialize_database(app, database_url=DEFAULT_DATABASE_URL)

    assert response.status_code == 422
    assert provider.requests == []


class ControlledMarketDataProvider:
    name = "controlled"

    def __init__(self, prices_by_symbol: dict[str, Sequence[DailyPrice]]) -> None:
        self._prices_by_symbol = prices_by_symbol
        self.requests: list[tuple[str, date | None]] = []

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        self.requests.append((symbol, start_date))
        return self._prices_by_symbol.get(symbol, ())


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


def _add_market_price(session: Session, *, etf_id: int, trade_date: date) -> None:
    session.add(
        MarketPrice(
            etf_id=etf_id,
            trade_date=trade_date,
            open_price=Decimal("100.000000"),
            high_price=Decimal("101.000000"),
            low_price=Decimal("99.000000"),
            close_price=Decimal("100.000000"),
            adjusted_close=None,
            volume=1000,
        )
    )


def _daily_price(symbol: str, *, trade_date: date) -> DailyPrice:
    return DailyPrice(
        symbol=symbol,
        trade_date=trade_date,
        open_price=Decimal("101.000000"),
        high_price=Decimal("102.000000"),
        low_price=Decimal("100.000000"),
        close_price=Decimal("101.500000"),
        adjusted_close=None,
        volume=2000,
    )
