from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import load_price_panel
from vela_core.models import Base, ETFInfo, MarketPrice


def test_loads_panel_for_single_etf_over_date_range() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 2), close_price=110)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 3), close_price=120)

        panel = load_price_panel(
            session,
            etf_ids=[etf.id],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
        )

    assert set(panel.keys()) == {etf.id}
    assert [row.trade_date for row in panel[etf.id]] == [
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 1, 3),
    ]
    assert [row.close_price for row in panel[etf.id]] == [
        Decimal("100"),
        Decimal("110"),
        Decimal("120"),
    ]


def test_loads_panel_for_multiple_etfs_grouped_by_etf_id() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        first = _add_etf(session, symbol="AAA")
        second = _add_etf(session, symbol="BBB")
        _add_price(session, etf_id=first.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(session, etf_id=first.id, trade_date=date(2026, 1, 3), close_price=120)
        _add_price(session, etf_id=second.id, trade_date=date(2026, 1, 2), close_price=200)

        panel = load_price_panel(
            session,
            etf_ids=[first.id, second.id],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
        )

    assert set(panel.keys()) == {first.id, second.id}
    assert [row.trade_date for row in panel[first.id]] == [date(2026, 1, 1), date(2026, 1, 3)]
    assert [row.trade_date for row in panel[second.id]] == [date(2026, 1, 2)]


def test_excludes_etfs_with_no_rows_in_range() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        first = _add_etf(session, symbol="AAA")
        second = _add_etf(session, symbol="BBB")
        _add_price(session, etf_id=first.id, trade_date=date(2026, 1, 1), close_price=100)
        _add_price(
            session, etf_id=second.id, trade_date=date(2025, 12, 31), close_price=999
        )

        panel = load_price_panel(
            session,
            etf_ids=[first.id, second.id],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )

    assert set(panel.keys()) == {first.id}


def test_returns_empty_panel_for_empty_etf_id_list() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        panel = load_price_panel(
            session,
            etf_ids=[],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
        )

    assert panel == {}


def test_returns_empty_panel_when_no_prices_match_range() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="AAA")
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)

        panel = load_price_panel(
            session,
            etf_ids=[etf.id],
            start_date=date(2030, 1, 1),
            end_date=date(2030, 1, 31),
        )

    assert panel == {}


def test_respects_start_and_end_date_bounds() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="AAA")
        for offset, close in enumerate([100, 110, 120, 130, 140]):
            _add_price(
                session,
                etf_id=etf.id,
                trade_date=date(2026, 1, 1) + timedelta(days=offset),
                close_price=close,
            )

        panel = load_price_panel(
            session,
            etf_ids=[etf.id],
            start_date=date(2026, 1, 2),
            end_date=date(2026, 1, 4),
        )

    assert [row.close_price for row in panel[etf.id]] == [
        Decimal("110"),
        Decimal("120"),
        Decimal("130"),
    ]


def test_accepts_none_start_date_as_unbounded_lower() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        etf = _add_etf(session, symbol="AAA")
        _add_price(session, etf_id=etf.id, trade_date=date(2020, 1, 1), close_price=50)
        _add_price(session, etf_id=etf.id, trade_date=date(2026, 1, 1), close_price=100)

        panel = load_price_panel(
            session,
            etf_ids=[etf.id],
            start_date=None,
            end_date=date(2026, 1, 1),
        )

    assert [row.trade_date for row in panel[etf.id]] == [
        date(2020, 1, 1),
        date(2026, 1, 1),
    ]


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


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


def _add_price(
    session: Session,
    *,
    etf_id: int,
    trade_date: date,
    close_price: int,
) -> None:
    session.add(
        MarketPrice(
            etf_id=etf_id,
            trade_date=trade_date,
            open_price=Decimal(close_price),
            high_price=Decimal(close_price),
            low_price=Decimal(close_price),
            close_price=Decimal(close_price),
            adjusted_close=None,
            volume=1000,
        )
    )