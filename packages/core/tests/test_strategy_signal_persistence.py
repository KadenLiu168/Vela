from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    StrategySignalPositionInput,
    get_latest_successful_strategy_signal,
    link_signals_to_backtest_run,
    persist_strategy_signal,
)
from vela_core.models import BacktestRun, Base, ETFInfo, StrategySignal, StrategySignalPosition


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
            source="manual",
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
    assert signal.source == "manual"
    assert signal.backtest_run_id is None
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
            source="manual",
            positions=[],
        )
        session.commit()

        signal_count = session.query(StrategySignal).count()
        position_count = session.query(StrategySignalPosition).count()

    assert result.positions == []
    assert signal_count == 1
    assert position_count == 0


def test_persist_strategy_signal_writes_scheduled_and_backtest_provenance() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        scheduled = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="hold",
            source="scheduled",
            positions=[],
        )
        backtest = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 24),
            config_version="v1",
            generated_at=datetime(2026, 6, 24, 9, 30, tzinfo=UTC),
            status="success",
            result="hold",
            source="backtest",
            backtest_run_id=run.id,
            positions=[],
        )

    assert scheduled.strategy_signal.source == "scheduled"
    assert scheduled.strategy_signal.backtest_run_id is None
    assert backtest.strategy_signal.source == "backtest"
    assert backtest.strategy_signal.backtest_run_id == run.id


@pytest.mark.parametrize("source", ["legacy", "unknown"])
def test_persist_strategy_signal_rejects_non_runtime_source_before_add(source: str) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        with pytest.raises(ValueError, match="Unsupported strategy signal source"):
            persist_strategy_signal(
                session,
                strategy_id="Dual_momentum",
                signal_date=date(2026, 6, 23),
                config_version="v1",
                generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                status="success",
                result="hold",
                source=source,
                positions=[],
            )

        assert list(session.new) == []


@pytest.mark.parametrize("source", ["manual", "scheduled"])
def test_persist_strategy_signal_rejects_live_source_with_backtest_link_before_add(
    source: str,
) -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        with pytest.raises(ValueError, match="Only backtest signals"):
            persist_strategy_signal(
                session,
                strategy_id="Dual_momentum",
                signal_date=date(2026, 6, 23),
                config_version="v1",
                generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
                status="success",
                result="hold",
                source=source,
                backtest_run_id=1,
                positions=[],
            )

        assert list(session.new) == []


def test_link_signals_to_backtest_run_links_only_distinct_unlinked_backtest_ids() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        run = _add_backtest_run(session)
        first = _persist_empty_signal(session, source="backtest", signal_date=date(2026, 6, 23))
        second = _persist_empty_signal(session, source="backtest", signal_date=date(2026, 6, 24))
        manual = _persist_empty_signal(session, source="manual", signal_date=date(2026, 6, 25))

        link_signals_to_backtest_run(
            session,
            run_id=run.id,
            signal_ids=[second.id, first.id, second.id],
        )
        session.flush()

        assert first.backtest_run_id == run.id
        assert second.backtest_run_id == run.id
        assert first.source == "backtest"
        assert second.source == "backtest"
        assert manual.backtest_run_id is None


def test_link_signals_to_backtest_run_rejects_missing_non_backtest_or_linked_ids() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        first_run = _add_backtest_run(session)
        second_run = _add_backtest_run(session, config_version="v2")
        linked = _persist_empty_signal(
            session,
            source="backtest",
            signal_date=date(2026, 6, 23),
            backtest_run_id=first_run.id,
        )
        manual = _persist_empty_signal(session, source="manual", signal_date=date(2026, 6, 24))

        for invalid_id in [999, manual.id, linked.id]:
            with pytest.raises(ValueError, match="Could not link every generated signal"):
                link_signals_to_backtest_run(
                    session,
                    run_id=second_run.id,
                    signal_ids=[invalid_id],
                )


def test_link_signals_to_backtest_run_empty_input_is_noop() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        link_signals_to_backtest_run(session, run_id=999, signal_ids=[])


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
            source="manual",
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
            source="manual",
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
            source="manual",
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
            source="manual",
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
            strategy_id="Dual_momentum",
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
            source="manual",
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
            source="manual",
            positions=[],
            error_message="missing market data",
        )
        session.commit()

        signal = get_latest_successful_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            strategy_id="Dual_momentum",
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
            source="manual",
            positions=[],
            error_message="missing market data",
        )
        session.commit()

        signal = get_latest_successful_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            strategy_id="Dual_momentum",
            config_version="v1",
        )

    assert signal is None


def test_get_latest_successful_strategy_signal_scopes_to_exact_strategy_id() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        matching = persist_strategy_signal(
            session,
            strategy_id="Dual_momentum",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
            status="success",
            result="rebalance",
            source="manual",
            positions=[],
        )
        persist_strategy_signal(
            session,
            strategy_id="Other_strategy",
            signal_date=date(2026, 6, 23),
            config_version="v1",
            generated_at=datetime(2026, 6, 23, 9, 35, tzinfo=UTC),
            status="success",
            result="hold",
            source="manual",
            positions=[],
        )
        session.commit()

        signal = get_latest_successful_strategy_signal(
            session,
            signal_date=date(2026, 6, 23),
            strategy_id="Dual_momentum",
            config_version="v1",
        )

    assert signal is not None
    assert signal.id == matching.strategy_signal.id


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


def _add_backtest_run(session: Session, *, config_version: str = "v1") -> BacktestRun:
    run = BacktestRun(
        strategy_id="Dual_momentum",
        config_version=config_version,
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 30),
        parameters_json="{}",
        started_at=datetime(2026, 7, 1, 9, 0, tzinfo=UTC),
        finished_at=datetime(2026, 7, 1, 9, 5, tzinfo=UTC),
        status="success",
    )
    session.add(run)
    session.flush()
    return run


def _persist_empty_signal(
    session: Session,
    *,
    source: str,
    signal_date: date,
    backtest_run_id: int | None = None,
) -> StrategySignal:
    return persist_strategy_signal(
        session,
        strategy_id="Dual_momentum",
        signal_date=signal_date,
        config_version="v1",
        generated_at=datetime(2026, 6, 23, 9, 30, tzinfo=UTC),
        status="success",
        result="hold",
        source=source,
        backtest_run_id=backtest_run_id,
        positions=[],
    ).strategy_signal
