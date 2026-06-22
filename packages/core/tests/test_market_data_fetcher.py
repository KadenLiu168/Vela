from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import DailyPrice, fetch_market_prices
from vela_core.models import Base, DataFetchLog, ETFInfo, MarketPrice


def test_fetch_market_prices_logs_successful_full_fetch() -> None:
    session_factory = _create_session_factory()
    provider = FakeMarketDataProvider(
        [
            _daily_price(symbol="SPY", trade_date=date(2026, 6, 17)),
            _daily_price(symbol="SPY", trade_date=date(2026, 6, 18)),
        ]
    )

    with session_factory() as session:
        _add_etf(session, symbol="SPY")

        result = fetch_market_prices(
            session,
            provider=provider,
            fetch_mode="full",
            symbols=["SPY"],
            start_date=date(2026, 6, 17),
            end_date=date(2026, 6, 18),
        )
        session.commit()

        log = session.query(DataFetchLog).one()

    assert result.status == "success"
    assert result.rows_fetched == 2
    assert result.rows_inserted == 2
    assert result.rows_updated == 0
    assert log.id == result.fetch_log_id
    assert log.source == "fake"
    assert log.target_type == "market_price"
    assert log.fetch_mode == "full"
    assert log.range_start == date(2026, 6, 17)
    assert log.range_end == date(2026, 6, 18)
    assert log.requested_symbols == '["SPY"]'
    assert log.status == "success"
    assert log.rows_fetched == 2
    assert log.rows_inserted == 2
    assert log.rows_updated == 0
    assert log.error_message is None
    assert log.finished_at is not None


def test_fetch_market_prices_logs_successful_incremental_fetch() -> None:
    session_factory = _create_session_factory()
    provider = FakeMarketDataProvider([_daily_price(symbol="SPY")])

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        session.add(_market_price(etf_id=etf.id, close_price=Decimal("499.00")))
        session.flush()

        result = fetch_market_prices(
            session,
            provider=provider,
            fetch_mode="incremental",
            symbols=["SPY"],
            start_date=date(2026, 6, 18),
            end_date=date(2026, 6, 18),
        )
        session.commit()

        log = session.query(DataFetchLog).one()
        price = session.query(MarketPrice).one()

    assert result.status == "success"
    assert result.rows_fetched == 1
    assert result.rows_inserted == 0
    assert result.rows_updated == 1
    assert log.fetch_mode == "incremental"
    assert log.status == "success"
    assert log.rows_fetched == 1
    assert log.rows_inserted == 0
    assert log.rows_updated == 1
    assert price.close_price == Decimal("100.500000")


def test_fetch_market_prices_logs_failed_fetch() -> None:
    session_factory = _create_session_factory()
    provider = FailingMarketDataProvider(failing_symbols={"SPY"})

    with session_factory() as session:
        _add_etf(session, symbol="SPY")

        result = fetch_market_prices(
            session,
            provider=provider,
            fetch_mode="incremental",
            symbols=["SPY"],
            start_date=date(2026, 6, 18),
            end_date=date(2026, 6, 18),
        )
        session.commit()

        log = session.query(DataFetchLog).one()
        market_price_count = session.query(MarketPrice).count()

    assert result.status == "failed"
    assert result.rows_fetched == 0
    assert result.rows_inserted == 0
    assert result.rows_updated == 0
    assert result.error_message == "SPY: provider failed for SPY"
    assert log.status == "failed"
    assert log.error_message == "SPY: provider failed for SPY"
    assert log.finished_at is not None
    assert market_price_count == 0


def test_fetch_market_prices_logs_partial_fetch() -> None:
    session_factory = _create_session_factory()
    provider = PartiallyFailingMarketDataProvider(
        prices=[_daily_price(symbol="SPY")],
        failing_symbols={"QQQ"},
    )

    with session_factory() as session:
        _add_etf(session, symbol="SPY")
        _add_etf(session, symbol="QQQ")

        result = fetch_market_prices(
            session,
            provider=provider,
            fetch_mode="incremental",
            symbols=["SPY", "QQQ"],
            start_date=date(2026, 6, 18),
            end_date=date(2026, 6, 18),
        )
        session.commit()

        log = session.query(DataFetchLog).one()
        prices = session.query(MarketPrice).all()

    assert result.status == "partial"
    assert result.rows_fetched == 1
    assert result.rows_inserted == 1
    assert result.rows_updated == 0
    assert result.error_message == "QQQ: provider failed for QQQ"
    assert log.requested_symbols == '["SPY", "QQQ"]'
    assert log.status == "partial"
    assert log.rows_fetched == 1
    assert log.rows_inserted == 1
    assert log.rows_updated == 0
    assert log.error_message == "QQQ: provider failed for QQQ"
    assert len(prices) == 1


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


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


def _daily_price(
    *,
    symbol: str,
    trade_date: date = date(2026, 6, 18),
) -> DailyPrice:
    return DailyPrice(
        symbol=symbol,
        trade_date=trade_date,
        open_price=Decimal("100.00"),
        high_price=Decimal("101.00"),
        low_price=Decimal("99.00"),
        close_price=Decimal("100.50"),
        volume=1000,
    )


def _market_price(*, etf_id: int, close_price: Decimal) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=date(2026, 6, 18),
        open_price=Decimal("100.00"),
        high_price=Decimal("101.00"),
        low_price=Decimal("99.00"),
        close_price=close_price,
        volume=1000,
    )


class FakeMarketDataProvider:
    name = "fake"

    def __init__(self, prices: Sequence[DailyPrice]) -> None:
        self._prices = prices

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        return [
            price
            for price in self._prices
            if price.symbol == symbol
            and (start_date is None or price.trade_date >= start_date)
            and (end_date is None or price.trade_date <= end_date)
        ]


class FailingMarketDataProvider:
    name = "fake"

    def __init__(self, *, failing_symbols: set[str]) -> None:
        self._failing_symbols = failing_symbols

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        if symbol in self._failing_symbols:
            raise RuntimeError(f"provider failed for {symbol}")
        return []


class PartiallyFailingMarketDataProvider(FakeMarketDataProvider):
    def __init__(self, prices: Sequence[DailyPrice], *, failing_symbols: set[str]) -> None:
        super().__init__(prices)
        self._failing_symbols = failing_symbols

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        if symbol in self._failing_symbols:
            raise RuntimeError(f"provider failed for {symbol}")
        return super().get_etf_daily_prices(symbol, start_date=start_date, end_date=end_date)
