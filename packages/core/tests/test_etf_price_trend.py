from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import get_etf_price_trend
from vela_core.models import Base, ETFInfo, MarketPrice


def test_etf_price_trend_returns_backward_adjusted_price_at_query_time() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        session.add(
            _market_price(
                etf_id=etf.id,
                trade_date=date(2026, 6, 23),
                close_price=Decimal("100.000000"),
                factor_hfq=Decimal("2.000000000000"),
            )
        )
        session.commit()

        result = get_etf_price_trend(session, etf_id=etf.id, range_="max")

    assert result is not None
    assert result.etf_id == etf.id
    assert result.exchange == "NYSEARCA"
    assert result.symbol == "SPY"
    assert result.name == "SPY ETF"
    assert [point.trade_date for point in result.points] == [date(2026, 6, 23)]
    # price == close_price * factor_hfq, derived at query time, never persisted
    assert result.points[0].price == Decimal("100.000000") * Decimal("2.000000000000")


def test_etf_price_trend_range_windows_anchor_at_latest_trade_date() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        session.add_all(
            [
                _market_price(etf_id=etf.id, trade_date=date(2025, 1, 10)),
                _market_price(etf_id=etf.id, trade_date=date(2026, 1, 10)),
                _market_price(etf_id=etf.id, trade_date=date(2026, 4, 15)),
                _market_price(etf_id=etf.id, trade_date=date(2026, 6, 23)),
            ]
        )
        session.commit()

        three_month = get_etf_price_trend(session, etf_id=etf.id, range_="3m")
        one_year = get_etf_price_trend(session, etf_id=etf.id, range_="1y")
        maximum = get_etf_price_trend(session, etf_id=etf.id, range_="max")

    assert three_month is not None
    assert [point.trade_date for point in three_month.points] == [
        date(2026, 4, 15),
        date(2026, 6, 23),
    ]
    assert one_year is not None
    assert [point.trade_date for point in one_year.points] == [
        date(2026, 1, 10),
        date(2026, 4, 15),
        date(2026, 6, 23),
    ]
    assert maximum is not None
    assert [point.trade_date for point in maximum.points] == [
        date(2025, 1, 10),
        date(2026, 1, 10),
        date(2026, 4, 15),
        date(2026, 6, 23),
    ]


def test_etf_price_trend_returns_empty_points_when_etf_has_no_prices() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        session.commit()

        result = get_etf_price_trend(session, etf_id=etf.id, range_="1y")

    assert result is not None
    assert result.etf_id == etf.id
    assert result.symbol == "SPY"
    assert result.points == ()


def test_etf_price_trend_returns_none_for_unknown_etf() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        result = get_etf_price_trend(session, etf_id=999, range_="1y")

    assert result is None


def test_etf_price_trend_default_range_is_one_year() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        session.add_all(
            [
                _market_price(etf_id=etf.id, trade_date=date(2025, 1, 10)),
                _market_price(etf_id=etf.id, trade_date=date(2026, 6, 23)),
            ]
        )
        session.commit()

        default_result = get_etf_price_trend(session, etf_id=etf.id)
        explicit_result = get_etf_price_trend(session, etf_id=etf.id, range_="1y")

    assert default_result is not None
    assert explicit_result is not None
    assert [point.trade_date for point in default_result.points] == [
        point.trade_date for point in explicit_result.points
    ]


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _add_etf(session: Session, *, symbol: str) -> ETFInfo:
    etf = ETFInfo(
        exchange="NYSEARCA",
        symbol=symbol,
        name=f"{symbol} ETF",
        currency="USD",
    )
    session.add(etf)
    session.flush()
    return etf


def _market_price(
    *,
    etf_id: int,
    trade_date: date,
    close_price: Decimal = Decimal("100.000000"),
    factor_hfq: Decimal = Decimal("1"),
) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=close_price,
        high_price=close_price,
        low_price=close_price,
        close_price=close_price,
        factor_hfq=factor_hfq,
        volume=1000,
    )
