import json
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    DailyPrice,
    MarketDataProviderError,
    fetch_full_market_prices,
    fetch_incremental_market_prices,
)
from vela_core.models import Base, DataFetchLog, ETFInfo, MarketPrice


def test_fetch_full_market_prices_uses_only_active_etfs() -> None:
    session_factory = _create_session_factory()
    provider = RecordingMarketDataProvider([_daily_price(symbol="SPY")])

    with session_factory() as session:
        _add_etf(session, symbol="SPY", is_active=True)
        _add_etf(session, symbol="QQQ", is_active=False)

        result = fetch_full_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()

    assert provider.requested_symbols == ["SPY"]
    assert result.status == "success"
    assert result.requested_symbol_count == 1
    assert log.requested_symbols == '["SPY"]'


def test_fetch_full_market_prices_maps_and_upserts_provider_rows() -> None:
    session_factory = _create_session_factory()
    provider = RecordingMarketDataProvider(
        [
            _daily_price(symbol="SPY", trade_date=date(2026, 6, 17)),
            _daily_price(symbol="SPY", trade_date=date(2026, 6, 18)),
        ]
    )

    with session_factory() as session:
        _add_etf(session, symbol="SPY")

        result = fetch_full_market_prices(session, provider=provider)
        session.commit()

        prices = session.query(MarketPrice).order_by(MarketPrice.trade_date).all()

    assert result.rows_fetched == 2
    assert result.rows_inserted == 2
    assert result.rows_updated == 0
    assert [price.trade_date for price in prices] == [date(2026, 6, 17), date(2026, 6, 18)]
    assert {price.close_price for price in prices} == {Decimal("100.500000")}


def test_fetch_full_market_prices_logs_successful_full_fetch() -> None:
    session_factory = _create_session_factory()
    provider = RecordingMarketDataProvider([_daily_price(symbol="SPY")])

    with session_factory() as session:
        _add_etf(session, symbol="SPY")

        result = fetch_full_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()

    assert result.status == "success"
    assert result.fetch_log_id == log.id
    assert result.requested_symbol_count == 1
    assert result.rows_fetched == 1
    assert result.rows_inserted == 1
    assert result.rows_updated == 0
    assert result.failed_symbols == ()
    assert result.error_message is None
    assert log.source == "fake"
    assert log.target_type == "market_price"
    assert log.fetch_mode == "full"
    assert log.range_start is None
    assert log.range_end is None
    assert log.requested_symbols == '["SPY"]'
    assert log.status == "success"
    assert log.rows_fetched == 1
    assert log.rows_inserted == 1
    assert log.rows_updated == 0
    assert log.error_message is None
    assert log.finished_at is not None


def test_fetch_full_market_prices_fails_when_no_active_etfs_exist() -> None:
    session_factory = _create_session_factory()
    provider = RecordingMarketDataProvider([])

    with session_factory() as session:
        _add_etf(session, symbol="SPY", is_active=False)

        result = fetch_full_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()

    assert provider.requested_symbols == []
    assert result.status == "failed"
    assert result.requested_symbol_count == 0
    assert result.rows_fetched == 0
    assert result.rows_inserted == 0
    assert result.rows_updated == 0
    assert result.error_message == "No active ETFs found"
    assert log.status == "failed"
    assert log.requested_symbols == "[]"
    assert log.error_message == "No active ETFs found"
    assert log.finished_at is not None


def test_fetch_full_market_prices_fails_when_no_requested_etf_succeeds() -> None:
    session_factory = _create_session_factory()
    provider = FailingMarketDataProvider(failing_symbols={"SPY"})

    with session_factory() as session:
        _add_etf(session, symbol="SPY")

        result = fetch_full_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()

    assert result.status == "failed"
    assert result.requested_symbol_count == 1
    assert result.rows_fetched == 0
    assert result.rows_inserted == 0
    assert result.rows_updated == 0
    assert result.failed_symbols == ("SPY",)
    assert result.error_message == "SPY: provider failed for SPY"
    assert log.status == "failed"
    assert log.rows_fetched == 0
    assert log.rows_inserted == 0
    assert log.rows_updated == 0
    assert log.error_message == "SPY: provider failed for SPY"


def test_fetch_full_market_prices_logs_provider_error_after_retry_exhaustion() -> None:
    session_factory = _create_session_factory()
    provider = ExhaustedRetryMarketDataProvider()

    with session_factory() as session:
        _add_etf(session, symbol="SPY")

        result = fetch_full_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()

    assert result.status == "failed"
    assert result.failed_symbols == ("SPY",)
    assert result.error_message == "SPY: akshare market data provider error symbol=SPY"
    assert log.status == "failed"
    assert log.error_message == "SPY: akshare market data provider error symbol=SPY"


def test_fetch_full_market_prices_fails_when_no_rows_are_fetched() -> None:
    session_factory = _create_session_factory()
    provider = RecordingMarketDataProvider([])

    with session_factory() as session:
        _add_etf(session, symbol="SPY")

        result = fetch_full_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()

    assert result.status == "failed"
    assert result.requested_symbol_count == 1
    assert result.rows_fetched == 0
    assert result.rows_inserted == 0
    assert result.rows_updated == 0
    assert result.failed_symbols == ()
    assert result.error_message == "No market prices fetched"
    assert log.status == "failed"
    assert log.error_message == "No market prices fetched"


def test_fetch_full_market_prices_logs_partial_fetch() -> None:
    session_factory = _create_session_factory()
    provider = PartiallyFailingMarketDataProvider(
        prices=[_daily_price(symbol="SPY")],
        failing_symbols={"QQQ"},
    )

    with session_factory() as session:
        _add_etf(session, symbol="SPY")
        _add_etf(session, symbol="QQQ")

        result = fetch_full_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()
        prices = session.query(MarketPrice).all()

    assert provider.requested_symbols == ["QQQ", "SPY"]
    assert result.status == "partial"
    assert result.requested_symbol_count == 2
    assert result.rows_fetched == 1
    assert result.rows_inserted == 1
    assert result.rows_updated == 0
    assert result.failed_symbols == ("QQQ",)
    assert result.error_message == "QQQ: provider failed for QQQ"
    assert log.requested_symbols == '["QQQ", "SPY"]'
    assert log.status == "partial"
    assert log.rows_fetched == 1
    assert log.rows_inserted == 1
    assert log.rows_updated == 0
    assert log.error_message == "QQQ: provider failed for QQQ"
    assert len(prices) == 1


def test_fetch_incremental_market_prices_uses_latest_local_trade_date() -> None:
    session_factory = _create_session_factory()
    provider = RecordingMarketDataProvider(
        [
            _daily_price(symbol="SPY", trade_date=date(2026, 6, 18)),
            _daily_price(symbol="SPY", trade_date=date(2026, 6, 19)),
        ]
    )

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_market_price(session, etf_id=etf.id, trade_date=date(2026, 6, 17))

        result = fetch_incremental_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()
        prices = session.query(MarketPrice).order_by(MarketPrice.trade_date).all()

    assert provider.requested_ranges == [("SPY", date(2026, 6, 18), date.today())]
    assert result.status == "success"
    assert result.rows_fetched == 2
    assert result.rows_inserted == 2
    assert result.rows_updated == 0
    assert [price.trade_date for price in prices] == [
        date(2026, 6, 17),
        date(2026, 6, 18),
        date(2026, 6, 19),
    ]
    assert log.fetch_mode == "incremental"
    assert log.range_start == date(2026, 6, 18)
    assert log.range_end == date.today()
    assert log.requested_symbols == '["SPY"]'


def test_fetch_incremental_market_prices_fails_without_local_baseline() -> None:
    session_factory = _create_session_factory()
    provider = RecordingMarketDataProvider([_daily_price(symbol="SPY")])

    with session_factory() as session:
        _add_etf(session, symbol="SPY")

        result = fetch_incremental_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()

    assert provider.requested_symbols == []
    assert result.status == "failed"
    assert result.requested_symbol_count == 1
    assert result.rows_fetched == 0
    assert result.rows_inserted == 0
    assert result.rows_updated == 0
    assert result.error_message == "No local market price baseline found"
    assert log.fetch_mode == "incremental"
    assert log.status == "failed"
    assert log.range_start is None
    assert log.range_end == date.today()
    assert log.error_message == "No local market price baseline found"


def test_fetch_incremental_market_prices_uses_only_active_etfs() -> None:
    session_factory = _create_session_factory()
    provider = RecordingMarketDataProvider(
        [
            _daily_price(symbol="SPY", trade_date=date(2026, 6, 18)),
            _daily_price(symbol="QQQ", trade_date=date(2026, 6, 18)),
        ]
    )

    with session_factory() as session:
        active_etf = _add_etf(session, symbol="SPY", is_active=True)
        _add_etf(session, symbol="QQQ", is_active=False)
        _add_market_price(session, etf_id=active_etf.id, trade_date=date(2026, 6, 17))

        result = fetch_incremental_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()
        prices = session.query(MarketPrice).order_by(MarketPrice.trade_date).all()

    assert provider.requested_symbols == ["SPY"]
    assert result.status == "success"
    assert result.requested_symbol_count == 1
    assert result.rows_fetched == 1
    assert result.rows_inserted == 1
    assert [price.trade_date for price in prices] == [date(2026, 6, 17), date(2026, 6, 18)]
    assert log.requested_symbols == '["SPY"]'


def test_fetch_incremental_market_prices_updates_existing_rows_without_duplicates() -> None:
    session_factory = _create_session_factory()
    provider = RecordingMarketDataProvider(
        [_daily_price(symbol="SPY", trade_date=date(2026, 6, 18))]
    )

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_market_price(session, etf_id=etf.id, trade_date=date(2026, 6, 17))

        first_result = fetch_incremental_market_prices(session, provider=provider)
        second_result = fetch_incremental_market_prices(session, provider=provider)
        session.commit()

        prices = session.query(MarketPrice).order_by(MarketPrice.trade_date).all()

    assert first_result.status == "success"
    assert first_result.rows_fetched == 1
    assert first_result.rows_inserted == 1
    assert first_result.rows_updated == 0
    assert second_result.status == "failed"
    assert second_result.rows_fetched == 0
    assert second_result.rows_inserted == 0
    assert second_result.rows_updated == 0
    assert len(prices) == 2
    assert [price.trade_date for price in prices] == [date(2026, 6, 17), date(2026, 6, 18)]


def test_fetch_incremental_market_prices_logs_partial_fetch() -> None:
    session_factory = _create_session_factory()
    provider = PartiallyFailingMarketDataProvider(
        prices=[_daily_price(symbol="SPY", trade_date=date(2026, 6, 18))],
        failing_symbols={"QQQ"},
    )

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_etf(session, symbol="QQQ")
        _add_market_price(session, etf_id=etf.id, trade_date=date(2026, 6, 17))

        result = fetch_incremental_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()
        prices = session.query(MarketPrice).order_by(MarketPrice.trade_date).all()

    assert provider.requested_symbols == ["QQQ", "SPY"]
    assert result.status == "partial"
    assert result.requested_symbol_count == 2
    assert result.rows_fetched == 1
    assert result.rows_inserted == 1
    assert result.rows_updated == 0
    assert result.failed_symbols == ("QQQ",)
    assert result.error_message == "QQQ: provider failed for QQQ"
    assert log.fetch_mode == "incremental"
    assert log.range_start == date(2026, 6, 18)
    assert log.range_end == date.today()
    assert log.status == "partial"
    assert log.error_message == "QQQ: provider failed for QQQ"
    assert [price.trade_date for price in prices] == [date(2026, 6, 17), date(2026, 6, 18)]


def test_fetch_full_market_prices_records_duplicate_trade_date_warnings() -> None:
    session_factory = _create_session_factory()
    provider = RecordingMarketDataProvider(
        [
            DailyPrice(
                symbol="SPY",
                trade_date=date(2026, 6, 18),
                open_price=Decimal("100.00"),
                high_price=Decimal("101.00"),
                low_price=Decimal("99.00"),
                close_price=Decimal("100.50"),
                volume=1000,
            ),
            DailyPrice(
                symbol="SPY",
                trade_date=date(2026, 6, 18),
                open_price=Decimal("200.00"),
                high_price=Decimal("201.00"),
                low_price=Decimal("199.00"),
                close_price=Decimal("200.50"),
                volume=2000,
            ),
        ]
    )

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        etf_id = etf.id

        result = fetch_full_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()
        prices = session.query(MarketPrice).all()

    assert result.quality_warnings is not None
    assert json.loads(result.quality_warnings) == {
        "duplicate_trade_dates": [{"etf_id": etf_id, "trade_date": "2026-06-18", "count": 2}]
    }
    assert log.quality_warnings == result.quality_warnings
    # Dedup semantics unchanged: one row persisted, last-write-wins keeps the second price.
    assert len(prices) == 1
    assert prices[0].close_price == Decimal("200.500000")


def test_fetch_full_market_prices_leaves_quality_warnings_null_without_duplicates() -> None:
    session_factory = _create_session_factory()
    provider = RecordingMarketDataProvider(
        [
            _daily_price(symbol="SPY", trade_date=date(2026, 6, 17)),
            _daily_price(symbol="SPY", trade_date=date(2026, 6, 18)),
        ]
    )

    with session_factory() as session:
        _add_etf(session, symbol="SPY")

        result = fetch_full_market_prices(session, provider=provider)
        session.commit()

        log = session.query(DataFetchLog).one()

    assert result.quality_warnings is None
    assert log.quality_warnings is None


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _add_etf(session: Session, symbol: str, *, is_active: bool = True) -> ETFInfo:
    etf = ETFInfo(
        exchange="NYSEARCA",
        symbol=symbol,
        name=f"{symbol} ETF",
        currency="USD",
        is_active=is_active,
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


def _add_market_price(session: Session, *, etf_id: int, trade_date: date) -> MarketPrice:
    market_price = MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=Decimal("100.00"),
        high_price=Decimal("101.00"),
        low_price=Decimal("99.00"),
        close_price=Decimal("100.50"),
        volume=1000,
    )
    session.add(market_price)
    session.flush()
    return market_price


class RecordingMarketDataProvider:
    name = "fake"

    def __init__(self, prices: Sequence[DailyPrice]) -> None:
        self._prices = prices
        self.requested_symbols: list[str] = []
        self.requested_ranges: list[tuple[str, date | None, date | None]] = []

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        self.requested_symbols.append(symbol)
        self.requested_ranges.append((symbol, start_date, end_date))
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


class ExhaustedRetryMarketDataProvider:
    name = "akshare"

    def get_etf_daily_prices(
        self,
        symbol: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> Sequence[DailyPrice]:
        raise MarketDataProviderError(f"akshare market data provider error symbol={symbol}")


class PartiallyFailingMarketDataProvider(RecordingMarketDataProvider):
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
        self.requested_symbols.append(symbol)
        self.requested_ranges.append((symbol, start_date, end_date))
        if symbol in self._failing_symbols:
            raise RuntimeError(f"provider failed for {symbol}")
        return [
            price
            for price in self._prices
            if price.symbol == symbol
            and (start_date is None or price.trade_date >= start_date)
            and (end_date is None or price.trade_date <= end_date)
        ]
