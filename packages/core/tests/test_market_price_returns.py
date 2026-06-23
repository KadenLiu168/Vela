from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import MarketPriceReturns, calculate_market_price_returns
from vela_core.models import Base, ETFInfo, MarketPrice


def test_calculates_complete_market_price_window_returns() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={
                0: Decimal("200"),
                60: Decimal("160"),
                100: Decimal("120"),
                120: Decimal("240"),
            },
            row_count=121,
        )

        returns = calculate_market_price_returns(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(120),
        )

    assert returns == MarketPriceReturns(
        etf_id=etf.id,
        as_of_date=_trade_date(120),
        return_20d=Decimal("1"),
        return_60d=Decimal("0.5"),
        return_120d=Decimal("0.2"),
    )


def test_returns_none_for_windows_with_insufficient_history() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={
                0: Decimal("75"),
                40: Decimal("100"),
                60: Decimal("150"),
            },
            row_count=61,
        )

        returns = calculate_market_price_returns(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(60),
        )

    assert returns.return_20d == Decimal("0.5")
    assert returns.return_60d == Decimal("1")
    assert returns.return_120d is None


def test_returns_none_for_all_windows_when_current_price_is_missing() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(session, etf_id=etf.id, prices_by_offset={}, row_count=121)

        returns = calculate_market_price_returns(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(130),
        )

    assert returns.return_20d is None
    assert returns.return_60d is None
    assert returns.return_120d is None


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
                20: Decimal("100"),
            },
            adjusted_close_by_offset={
                0: Decimal("75"),
                20: Decimal("150"),
            },
            row_count=21,
        )
        _add_price_history(
            session,
            etf_id=other_etf.id,
            prices_by_offset={
                0: Decimal("1"),
                20: Decimal("1000"),
            },
            row_count=21,
        )

        returns = calculate_market_price_returns(
            session,
            etf_id=target_etf.id,
            as_of_date=_trade_date(20),
        )

    assert returns.return_20d == Decimal("1")
    assert returns.return_60d is None
    assert returns.return_120d is None


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
