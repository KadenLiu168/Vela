from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    StrategySignalPositionInput,
    calculate_portfolio_holdings,
    persist_strategy_signal,
)
from vela_core.models import Base, ETFInfo


def test_calculate_daily_holdings_from_signal_positions() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("0.500000")),
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("0.500000")),
            ],
        )
        session.commit()

        snapshots = calculate_portfolio_holdings(
            session,
            trading_dates=[date(2026, 6, 23)],
            config_version="v1",
        )

    assert [snapshot.trade_date for snapshot in snapshots] == [date(2026, 6, 23)]
    assert snapshots[0].signal_date == date(2026, 6, 23)
    assert {holding.etf_id for holding in snapshots[0].holdings} == {spy.id, qqq.id}
    assert {holding.target_weight for holding in snapshots[0].holdings} == {
        Decimal("0.500000"),
    }


def test_calculate_interval_holdings_carries_positions_forward() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("1.000000")),
            ],
        )
        session.commit()

        snapshots = calculate_portfolio_holdings(
            session,
            trading_dates=[
                date(2026, 6, 23),
                date(2026, 6, 24),
                date(2026, 6, 25),
            ],
            config_version="v1",
        )

    assert [snapshot.signal_date for snapshot in snapshots] == [
        date(2026, 6, 23),
        date(2026, 6, 23),
        date(2026, 6, 23),
    ]
    assert [[holding.etf_id for holding in snapshot.holdings] for snapshot in snapshots] == [
        [spy.id],
        [spy.id],
        [spy.id],
    ]


def test_calculate_interval_holdings_empty_before_first_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 24),
            config_version="v1",
            generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("1.000000")),
            ],
        )
        session.commit()

        snapshots = calculate_portfolio_holdings(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            config_version="v1",
        )

    assert snapshots[0].signal_date is None
    assert snapshots[0].strategy_signal_id is None
    assert snapshots[0].holdings == []
    assert snapshots[1].signal_date == date(2026, 6, 24)
    assert [holding.etf_id for holding in snapshots[1].holdings] == [spy.id]


def test_calculate_interval_holdings_changes_on_rebalance_date() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("1.000000")),
            ],
        )
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 25),
            config_version="v1",
            generated_at=datetime(2026, 6, 25, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("1.000000")),
            ],
        )
        session.commit()

        snapshots = calculate_portfolio_holdings(
            session,
            trading_dates=[
                date(2026, 6, 24),
                date(2026, 6, 25),
                date(2026, 6, 26),
            ],
            config_version="v1",
        )

    assert [[holding.etf_id for holding in snapshot.holdings] for snapshot in snapshots] == [
        [spy.id],
        [qqq.id],
        [qqq.id],
    ]
    assert [snapshot.signal_date for snapshot in snapshots] == [
        date(2026, 6, 23),
        date(2026, 6, 25),
        date(2026, 6, 25),
    ]


def test_calculate_holdings_uses_latest_successful_signal_run_for_date() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("1.000000")),
            ],
        )
        latest = persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 35, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("1.000000")),
            ],
        )
        session.commit()

        snapshots = calculate_portfolio_holdings(
            session,
            trading_dates=[date(2026, 6, 23)],
            config_version="v1",
        )

    assert snapshots[0].strategy_signal_id == latest.strategy_signal.id
    assert [holding.etf_id for holding in snapshots[0].holdings] == [qqq.id]


def test_calculate_holdings_ignores_failed_signals() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("1.000000")),
            ],
        )
        persist_strategy_signal(
            session,
            signal_date=date(2026, 6, 24),
            config_version="v1",
            generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
            status="failed",
            result=None,
            positions=[
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("1.000000")),
            ],
            error_message="missing prices",
        )
        session.commit()

        snapshots = calculate_portfolio_holdings(
            session,
            trading_dates=[date(2026, 6, 24)],
            config_version="v1",
        )

    assert snapshots[0].signal_date == date(2026, 6, 23)
    assert [holding.etf_id for holding in snapshots[0].holdings] == [spy.id]


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
