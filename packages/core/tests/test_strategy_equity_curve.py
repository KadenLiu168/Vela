from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    StrategyEquityCurvePoint,
    StrategySignalPositionInput,
    calculate_strategy_equity_curve,
    persist_strategy_signal,
)
from vela_core.models import Base, ETFInfo, MarketPrice


def test_calculate_strategy_equity_curve_returns_empty_for_empty_dates() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[],
            config_version="v1",
        )

    assert points == []


def test_calculate_strategy_equity_curve_sets_initial_net_value() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=spy.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23)],
            config_version="v1",
        )

    assert points == [
        StrategyEquityCurvePoint(
            trade_date=date(2026, 6, 23),
            net_value=Decimal("1.000000"),
            daily_return=Decimal("0.000000"),
        )
    ]


def test_calculate_strategy_equity_curve_applies_weighted_daily_return() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        _add_signal(
            session,
            signal_date=date(2026, 6, 23),
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("0.600000")),
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("0.400000")),
            ],
        )
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=110)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 23), close_price=200)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 24), close_price=180)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            config_version="v1",
        )

    assert [point.net_value for point in points] == [
        Decimal("1.000000"),
        Decimal("1.020000"),
    ]
    assert points[1].daily_return == Decimal("0.020000")


def test_calculate_strategy_equity_curve_carries_and_rebalances_holdings() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=spy.id)
        _add_signal(session, signal_date=date(2026, 6, 25), etf_id=qqq.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 23), close_price=100)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=110)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 25), close_price=55)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 24), close_price=200)
        _add_price(session, etf_id=qqq.id, trade_date=date(2026, 6, 25), close_price=220)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[
                date(2026, 6, 23),
                date(2026, 6, 24),
                date(2026, 6, 25),
            ],
            config_version="v1",
        )

    assert [point.net_value for point in points] == [
        Decimal("1.000000"),
        Decimal("1.100000"),
        Decimal("1.210000"),
    ]


def test_calculate_strategy_equity_curve_keeps_net_value_for_empty_holdings() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 22), date(2026, 6, 23)],
            config_version="v1",
        )

    assert [point.net_value for point in points] == [
        Decimal("1.000000"),
        Decimal("1.000000"),
    ]
    assert points[1].daily_return == Decimal("0.000000")


def test_calculate_strategy_equity_curve_treats_missing_price_input_as_neutral() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        _add_signal(session, signal_date=date(2026, 6, 23), etf_id=spy.id)
        _add_price(session, etf_id=spy.id, trade_date=date(2026, 6, 24), close_price=110)
        session.commit()

        points = calculate_strategy_equity_curve(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            config_version="v1",
        )

    assert points[1].net_value == Decimal("1.000000")
    assert points[1].daily_return == Decimal("0.000000")


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


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


def _add_signal(
    session: Session,
    *,
    signal_date: date,
    etf_id: int | None = None,
    positions: list[StrategySignalPositionInput] | None = None,
) -> None:
    persist_strategy_signal(
        session,
        signal_date=signal_date,
        config_version="v1",
        generated_at=datetime.combine(signal_date, datetime.min.time(), tzinfo=UTC),
        status="success",
        result="rebalance",
        positions=positions
        if positions is not None
        else [
            StrategySignalPositionInput(
                etf_id=etf_id or 0,
                target_weight=Decimal("1.000000"),
            )
        ],
    )


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
