from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import MarketPriceMovingAverage, calculate_market_price_moving_average
from vela_core.models import Base, ETFInfo, MarketPrice


def test_calculates_complete_120_day_moving_average() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={
                0: Decimal("80"),
                1: Decimal("120"),
                2: Decimal("120"),
                119: Decimal("200"),
            },
            row_count=120,
        )

        moving_average = calculate_market_price_moving_average(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(119),
        )

    assert moving_average == MarketPriceMovingAverage(
        etf_id=etf.id,
        as_of_date=_trade_date(119),
        ma_120d=Decimal("101"),
    )


def test_returns_none_when_history_has_fewer_than_120_rows() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(session, etf_id=etf.id, prices_by_offset={}, row_count=119)

        moving_average = calculate_market_price_moving_average(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(118),
        )

    assert moving_average == MarketPriceMovingAverage(
        etf_id=etf.id,
        as_of_date=_trade_date(118),
        ma_120d=None,
    )


def test_ignores_prices_older_than_120_day_window() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={
                0: Decimal("1000"),
                1: Decimal("80"),
                2: Decimal("120"),
                3: Decimal("120"),
                120: Decimal("200"),
            },
            row_count=121,
        )

        moving_average = calculate_market_price_moving_average(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(120),
        )

    assert moving_average.ma_120d == Decimal("101")


def test_returns_none_when_current_price_is_missing() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(session, etf_id=etf.id, prices_by_offset={}, row_count=120)

        moving_average = calculate_market_price_moving_average(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(130),
        )

    assert moving_average == MarketPriceMovingAverage(
        etf_id=etf.id,
        as_of_date=_trade_date(130),
        ma_120d=None,
    )


def test_uses_adjusted_close_and_ignores_other_etf_histories() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        target_etf = _add_etf(session, symbol="SPY")
        other_etf = _add_etf(session, symbol="QQQ")
        _add_price_history(
            session,
            etf_id=target_etf.id,
            prices_by_offset={
                0: Decimal("100"),
                119: Decimal("100"),
            },
            adjusted_close_by_offset={
                0: Decimal("80"),
                1: Decimal("120"),
                2: Decimal("120"),
                119: Decimal("200"),
            },
            row_count=120,
        )
        _add_price_history(
            session,
            etf_id=other_etf.id,
            prices_by_offset={offset: Decimal("1000") for offset in range(120)},
            row_count=120,
        )

        moving_average = calculate_market_price_moving_average(
            session,
            etf_id=target_etf.id,
            as_of_date=_trade_date(119),
        )

    assert moving_average.ma_120d == Decimal("101")


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


def _add_price_history(
    session: Session,
    *,
    etf_id: int,
    prices_by_offset: dict[int, Decimal],
    row_count: int,
    adjusted_close_by_offset: dict[int, Decimal] | None = None,
) -> None:
    adjusted_close_by_offset = adjusted_close_by_offset or {}
    session.add_all(
        _market_price(
            etf_id=etf_id,
            trade_date=_trade_date(offset),
            close_price=prices_by_offset.get(offset, Decimal("100")),
            adjusted_close=adjusted_close_by_offset.get(offset),
        )
        for offset in range(row_count)
    )
    session.commit()


def _trade_date(offset: int) -> date:
    return date(2026, 1, 1) + timedelta(days=offset)


def _market_price(
    *,
    etf_id: int,
    trade_date: date,
    close_price: Decimal,
    adjusted_close: Decimal | None = None,
) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=close_price,
        high_price=close_price,
        low_price=close_price,
        close_price=close_price,
        adjusted_close=adjusted_close,
        volume=1000,
    )
