from datetime import UTC, date, datetime
from decimal import Decimal
from typing import cast

import pytest
from sqlalchemy import Table, UniqueConstraint, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from vela_core.models import Base, ETFInfo, StrategySignal, StrategySignalPosition


def test_strategy_signal_table_has_required_columns() -> None:
    table = cast(Table, StrategySignal.__table__)
    columns = set(table.columns.keys())

    assert {
        "id",
        "signal_date",
        "config_version",
        "generated_at",
        "status",
        "result",
        "error_message",
        "created_at",
        "updated_at",
    } <= columns


def test_strategy_signal_nullable_fields() -> None:
    table = cast(Table, StrategySignal.__table__)

    assert table.columns["result"].nullable is True
    assert table.columns["error_message"].nullable is True


def test_strategy_signal_supports_expected_status_values() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add_all(
            [
                _strategy_signal(status=status, config_version=f"v1-{status}")
                for status in StrategySignal.STATUSES
            ]
        )
        session.commit()

        statuses = {signal.status for signal in session.query(StrategySignal).all()}

    assert statuses == {"running", "success", "failed", "partial"}


def test_strategy_signal_supports_expected_result_values() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add_all(
            [
                _strategy_signal(result=result, config_version=f"v1-{result}")
                for result in StrategySignal.RESULTS
            ]
        )
        session.commit()

        results = {signal.result for signal in session.query(StrategySignal).all()}

    assert results == {"buy", "hold", "rebalance", "empty"}


def test_strategy_signal_allows_same_date_and_config_version_rerun() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        session.add_all(
            [
                _strategy_signal(generated_at=datetime(2026, 6, 18, 9, 30, tzinfo=UTC)),
                _strategy_signal(generated_at=datetime(2026, 6, 18, 9, 35, tzinfo=UTC)),
            ]
        )
        session.commit()

        assert session.query(StrategySignal).count() == 2


def test_strategy_signal_has_lookup_indexes() -> None:
    table = cast(Table, StrategySignal.__table__)
    indexed_columns = {tuple(column.name for column in index.columns) for index in table.indexes}

    assert ("signal_date", "config_version") in indexed_columns
    assert ("status", "generated_at") in indexed_columns


def test_strategy_signal_position_table_has_required_columns() -> None:
    table = cast(Table, StrategySignalPosition.__table__)
    columns = set(table.columns.keys())

    assert {
        "id",
        "strategy_signal_id",
        "etf_id",
        "rank",
        "score",
        "target_weight",
        "created_at",
    } <= columns


def test_strategy_signal_position_references_signal_and_etf() -> None:
    table = cast(Table, StrategySignalPosition.__table__)

    signal_foreign_keys = table.columns["strategy_signal_id"].foreign_keys
    etf_foreign_keys = table.columns["etf_id"].foreign_keys

    assert any(
        foreign_key.column.table.name == "strategy_signal" for foreign_key in signal_foreign_keys
    )
    assert any(foreign_key.column.table.name == "etf_info" for foreign_key in etf_foreign_keys)


def test_strategy_signal_position_optional_explanation_fields_are_nullable() -> None:
    table = cast(Table, StrategySignalPosition.__table__)

    assert table.columns["rank"].nullable is True
    assert table.columns["score"].nullable is True


def test_strategy_signal_position_has_signal_etf_unique_constraint() -> None:
    table = cast(Table, StrategySignalPosition.__table__)
    unique_constraints = [
        constraint for constraint in table.constraints if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        {column.name for column in constraint.columns} == {"strategy_signal_id", "etf_id"}
        for constraint in unique_constraints
    )


def test_strategy_signal_position_rejects_duplicate_etf_in_same_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        signal = _add_signal(session)
        etf = _add_etf(session, symbol="SPY")
        session.add(
            _strategy_signal_position(
                strategy_signal_id=signal.id,
                etf_id=etf.id,
            )
        )
        session.commit()

        session.add(
            _strategy_signal_position(
                strategy_signal_id=signal.id,
                etf_id=etf.id,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_strategy_signal_position_allows_same_etf_in_different_signals() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        first_signal = _add_signal(session, config_version="v1")
        second_signal = _add_signal(session, config_version="v2")
        etf = _add_etf(session, symbol="SPY")
        session.add_all(
            [
                _strategy_signal_position(
                    strategy_signal_id=first_signal.id,
                    etf_id=etf.id,
                ),
                _strategy_signal_position(
                    strategy_signal_id=second_signal.id,
                    etf_id=etf.id,
                ),
            ]
        )
        session.commit()

        assert session.query(StrategySignalPosition).count() == 2


def test_strategy_signal_position_allows_repeated_rank_in_same_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        signal = _add_signal(session)
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        session.add_all(
            [
                _strategy_signal_position(
                    strategy_signal_id=signal.id,
                    etf_id=spy.id,
                    rank=1,
                ),
                _strategy_signal_position(
                    strategy_signal_id=signal.id,
                    etf_id=qqq.id,
                    rank=1,
                ),
            ]
        )
        session.commit()

        assert session.query(StrategySignalPosition).count() == 2


def test_strategy_signal_position_has_lookup_indexes() -> None:
    table = cast(Table, StrategySignalPosition.__table__)
    indexed_columns = {tuple(column.name for column in index.columns) for index in table.indexes}

    assert ("strategy_signal_id",) in indexed_columns


def test_strategy_signal_positions_returns_related_position_rows() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        signal = _add_signal(session)
        spy = _add_etf(session, symbol="SPY")
        qqq = _add_etf(session, symbol="QQQ")
        expected_etf_ids = {spy.id, qqq.id}
        session.add_all(
            [
                _strategy_signal_position(
                    strategy_signal_id=signal.id,
                    etf_id=spy.id,
                ),
                _strategy_signal_position(
                    strategy_signal_id=signal.id,
                    etf_id=qqq.id,
                ),
            ]
        )
        session.commit()

        position_etf_ids = {position.etf_id for position in signal.positions}

    assert position_etf_ids == expected_etf_ids


def test_strategy_signal_position_strategy_signal_returns_parent_signal() -> None:
    session_factory = _create_session_factory()

    with session_factory() as session:
        signal = _add_signal(session)
        etf = _add_etf(session, symbol="SPY")
        expected_signal_id = signal.id
        position = _strategy_signal_position(
            strategy_signal_id=signal.id,
            etf_id=etf.id,
        )
        session.add(position)
        session.commit()

        parent_signal_id = position.strategy_signal.id

    assert parent_signal_id == expected_signal_id


def test_alembic_target_metadata_includes_strategy_signal_tables() -> None:
    import importlib.util
    from pathlib import Path

    env_path = Path(__file__).parents[3] / "alembic" / "env.py"
    spec = importlib.util.spec_from_file_location("alembic_env", env_path)

    assert spec is not None
    assert spec.loader is not None

    alembic_env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alembic_env)

    assert "strategy_signal" in alembic_env.target_metadata.tables
    assert "strategy_signal_position" in alembic_env.target_metadata.tables


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _add_signal(session: Session, config_version: str = "v1") -> StrategySignal:
    signal = _strategy_signal(config_version=config_version)
    session.add(signal)
    session.flush()
    return signal


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


def _strategy_signal(
    *,
    signal_date: date = date(2026, 6, 18),
    strategy_id: str = "Dual_momentum",
    config_version: str = "v1",
    generated_at: datetime = datetime(2026, 6, 18, 9, 30, tzinfo=UTC),
    status: str = "success",
    result: str | None = "rebalance",
    error_message: str | None = None,
) -> StrategySignal:
    return StrategySignal(
        signal_date=signal_date,
        strategy_id=strategy_id,
        config_version=config_version,
        generated_at=generated_at,
        status=status,
        result=result,
        error_message=error_message,
    )


def _strategy_signal_position(
    *,
    strategy_signal_id: int,
    etf_id: int,
    rank: int | None = None,
    score: Decimal | None = Decimal("0.750000"),
    target_weight: Decimal = Decimal("0.500000"),
) -> StrategySignalPosition:
    return StrategySignalPosition(
        strategy_signal_id=strategy_signal_id,
        etf_id=etf_id,
        rank=rank,
        score=score,
        target_weight=target_weight,
    )
