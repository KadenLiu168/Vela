from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    StrategySignalPositionInput,
    get_latest_successful_strategy_signal,
    persist_strategy_signal,
)
from vela_core.models import Base, ETFInfo, StrategySignal, StrategySignalPosition


def test_persist_strategy_signal_writes_signal_and_positions() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        spy_id = spy.id
        qqq_id = qqq.id
        result = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[
                StrategySignalPositionInput(
                    etf_id=spy_id,
                    rank=1,
                    score=Decimal("0.750000"),
                    target_weight=Decimal("0.500000"),
                ),
                StrategySignalPositionInput(
                    etf_id=qqq_id,
                    rank=2,
                    score=Decimal("0.500000"),
                    target_weight=Decimal("0.500000"),
                ),
            ],
        )
        session.commit()

        signal = session.get(StrategySignal, result.strategy_signal.id)
        positions = session.scalars(select(StrategySignalPosition)).all()

    assert signal is not None
    assert signal.signal_date == date(2026, 6, 23)
    assert signal.config_version == "v1"
    assert signal.status == "success"
    assert signal.result == "rebalance"
    assert len(positions) == 2
    assert {position.etf_id for position in positions} == {spy_id, qqq_id}
    assert {position.target_weight for position in positions} == {
        Decimal("0.500000"),
    }


def test_persist_strategy_signal_writes_signal_without_positions() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        result = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="empty",
            positions=[],
        )
        session.commit()

        signal_count = session.query(StrategySignal).count()
        position_count = session.query(StrategySignalPosition).count()

    assert result.positions == []
    assert signal_count == 1
    assert position_count == 0


def test_persist_strategy_signal_preserves_same_date_and_config_reruns() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[],
        )
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 35, tzinfo=UTC),
            status="success",
            result="hold",
            positions=[],
        )
        session.commit()

        signals = session.scalars(select(StrategySignal)).all()

    assert len(signals) == 2
    assert {signal.result for signal in signals} == {"rebalance", "hold"}


def test_get_latest_successful_strategy_signal_returns_newest_success_with_positions() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        spy_id = spy.id
        qqq_id = qqq.id
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="hold",
            positions=[
                StrategySignalPositionInput(
                    etf_id=spy_id,
                    rank=1,
                    score=Decimal("0.750000"),
                    target_weight=Decimal("1.000000"),
                )
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
            positions=[
                StrategySignalPositionInput(
                    etf_id=qqq_id,
                    rank=1,
                    score=Decimal("0.900000"),
                    target_weight=Decimal("1.000000"),
                )
            ],
        )
        session.commit()

        signal = get_latest_successful_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
        )

    assert signal is not None
    assert signal.id == latest.strategy_signal.id
    assert signal.result == "rebalance"
    assert [position.etf_id for position in signal.positions] == [qqq_id]


def test_get_latest_successful_strategy_signal_ignores_newer_non_success() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        success = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            positions=[],
        )
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 35, tzinfo=UTC),
            status="failed",
            result=None,
            positions=[],
            error_message="missing market data",
        )
        session.commit()

        signal = get_latest_successful_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
        )

    assert signal is not None
    assert signal.id == success.strategy_signal.id


def test_get_latest_successful_strategy_signal_returns_none_without_success() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="failed",
            result=None,
            positions=[],
            error_message="missing market data",
        )
        session.commit()

        signal = get_latest_successful_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            config_version="v1",
        )

    assert signal is None


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
