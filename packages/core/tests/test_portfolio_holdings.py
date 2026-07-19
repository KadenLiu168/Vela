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
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("0.500000")),
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("0.500000")),
            ],
        )
        session.commit()

        snapshots = calculate_portfolio_holdings(
            session,
            trading_dates=[date(2026, 6, 23)],
            strategy_id="Dual_momentum",
            config_version="v1",
        )

    assert [snapshot.trade_date for snapshot in snapshots] == [date(2026, 6, 23)]
    # T+1: a signal dated 06-23 does not apply on its own as-of date 06-23.
    assert snapshots[0].signal_date is None
    assert snapshots[0].strategy_signal_id is None
    assert snapshots[0].holdings == []


def test_calculate_interval_holdings_carries_positions_forward() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
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
            strategy_id="Dual_momentum",
            config_version="v1",
        )

    # T+1: 06-23 (the signal's own as-of day) is empty; 06-24/06-25 carry the 06-23 signal.
    assert [snapshot.signal_date for snapshot in snapshots] == [
        None,
        date(2026, 6, 23),
        date(2026, 6, 23),
    ]
    assert [[holding.etf_id for holding in snapshot.holdings] for snapshot in snapshots] == [
        [],
        [spy.id],
        [spy.id],
    ]


def test_calculate_interval_holdings_empty_before_first_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 24),
            config_version="v1",
            generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("1.000000")),
            ],
        )
        session.commit()

        snapshots = calculate_portfolio_holdings(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_id="Dual_momentum",
            config_version="v1",
        )

    # T+1: 06-23 precedes the first signal; 06-24 is the signal's own as-of day.
    # Both snapshots are empty.
    assert snapshots[0].signal_date is None
    assert snapshots[0].strategy_signal_id is None
    assert snapshots[0].holdings == []
    assert snapshots[1].signal_date is None
    assert snapshots[1].strategy_signal_id is None
    assert snapshots[1].holdings == []


def test_calculate_interval_holdings_changes_on_rebalance_date() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("1.000000")),
            ],
        )
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 25),
            config_version="v1",
            generated_at=datetime(2026, 6, 25, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
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
            strategy_id="Dual_momentum",
            config_version="v1",
        )

    # T+1: 06-24 uses the 06-23 signal (SPY); 06-25 carries SPY (the 06-25 signal
    # is same-day and not applied); 06-26 uses the 06-25 signal (QQQ).
    assert [[holding.etf_id for holding in snapshot.holdings] for snapshot in snapshots] == [
        [spy.id],
        [spy.id],
        [qqq.id],
    ]
    assert [snapshot.signal_date for snapshot in snapshots] == [
        date(2026, 6, 23),
        date(2026, 6, 23),
        date(2026, 6, 25),
    ]


def test_calculate_holdings_uses_latest_successful_signal_run_for_date() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("1.000000")),
            ],
        )
        latest = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 35, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("1.000000")),
            ],
        )
        session.commit()

        snapshots = calculate_portfolio_holdings(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_id="Dual_momentum",
            config_version="v1",
        )

    # T+1: 06-23 (the signal's own as-of day) does not apply the same-day signal.
    assert snapshots[0].signal_date is None
    assert snapshots[0].strategy_signal_id is None
    assert snapshots[0].holdings == []
    # 06-24 uses the LATEST successful run for 06-23 (QQQ), preserving the
    # "latest successful signal run wins" rule at T+1.
    assert snapshots[1].strategy_signal_id == latest.strategy_signal.id
    assert snapshots[1].signal_date == date(2026, 6, 23)
    assert [holding.etf_id for holding in snapshots[1].holdings] == [qqq.id]


def test_calculate_holdings_ignores_failed_signals() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("1.000000")),
            ],
        )
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 24),
            config_version="v1",
            generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
            status="failed",
            result=None,
            source="manual",
            positions=[
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("1.000000")),
            ],
            error_message="missing prices",
        )
        session.commit()

        snapshots = calculate_portfolio_holdings(
            session,
            trading_dates=[date(2026, 6, 24)],
            strategy_id="Dual_momentum",
            config_version="v1",
        )

    assert snapshots[0].signal_date == date(2026, 6, 23)
    assert [holding.etf_id for holding in snapshots[0].holdings] == [spy.id]


def test_calculate_holdings_ignores_newer_foreign_strategy_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        matching = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[
                StrategySignalPositionInput(etf_id=spy.id, target_weight=Decimal("1.000000"))
            ],
        )
        persist_strategy_signal(
            session,
            strategy_id="Other_strategy",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 35, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[
                StrategySignalPositionInput(etf_id=qqq.id, target_weight=Decimal("1.000000"))
            ],
        )
        session.commit()

        snapshots = calculate_portfolio_holdings(
            session,
            trading_dates=[date(2026, 6, 23), date(2026, 6, 24)],
            strategy_id="Dual_momentum",
            config_version="v1",
        )

    assert snapshots[0].holdings == []
    assert snapshots[1].strategy_signal_id == matching.strategy_signal.id
    assert [holding.etf_id for holding in snapshots[1].holdings] == [spy.id]


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
