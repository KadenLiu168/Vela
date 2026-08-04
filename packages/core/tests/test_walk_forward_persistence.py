from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from vela_core.models import BacktestBenchmark, BacktestRun, Base, WalkForwardRun
from vela_core.walk_forward.persistence import (
    WalkForwardPersistenceInput,
    WalkForwardWindowPersistenceInput,
    persist_walk_forward_run,
)


def _summary() -> dict[str, object]:
    return {
        "mean": 0.1,
        "median": 0.1,
        "min": 0.05,
        "max": 0.15,
        "std": 0.04,
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }


def _evidence() -> dict[str, object]:
    metrics = {
        name: _summary()
        for name in (
            "total_return",
            "annualized_return",
            "sharpe_ratio",
            "max_drawdown",
            "volatility",
            "sortino_ratio",
            "calmar_ratio",
            "longest_drawdown_duration_sessions",
        )
    }
    rate = {
        "numerator": 2,
        "denominator": 3,
        "value": 2 / 3,
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }
    comparison = {
        "total_return_difference": _summary(),
        "annualized_return_difference": _summary(),
        "tracking_error": _summary(),
        "information_ratio": _summary(),
        "outperformance_rate": rate,
    }
    return {
        "metrics": metrics,
        "positive_window_rate": rate,
        "generalization_gap": _summary(),
        "benchmarks": {"equal_weight_monthly": comparison, "csi_300_buy_hold": comparison},
        "parameter_stability": {},
    }


def _input(window_count: int = 1) -> WalkForwardPersistenceInput:
    windows = tuple(
        WalkForwardWindowPersistenceInput(
            ordinal=index,
            train_start=date(2025, 1, 1),
            train_end=date(2025, 12, 31),
            test_start=date(2026, 1, 1),
            test_end=date(2026, 12, 31),
            oos_version=f"wf-{index:012d}",
            selected_parameters={"parameters.selection.top_n": 1},
            candidate_count=1,
            eligible_count=1,
            skipped_count=0,
            skip_reason_counts={},
            train_sharpe=Decimal("1.2"),
            oos_backtest_run_id=index + 1,
        )
        for index in range(window_count)
    )
    return WalkForwardPersistenceInput(
        strategy_id="demo",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        window_count=window_count,
        walk_forward_config={"window": {"start_date": "2026-01-01"}},
        base_strategy_config={"strategy_id": "demo"},
        config_checksum="a" * 64,
        input_data_snapshot={
            "version": "wf_provenance_v1",
            "earliest_required_session": "2025-01-01",
            "configured_end_date": "2026-12-31",
            "following_session": None,
            "official_sessions": ["2025-01-01"],
            "active_etfs": [],
            "loaded_price_row_count": 0,
            "first_loaded_price_date": None,
            "last_loaded_price_date": None,
        },
        input_data_checksum="b" * 64,
        evidence=_evidence(),
        started_at=datetime(2026, 1, 1),
        finished_at=datetime(2026, 1, 2),
        windows=windows,
    )


def _seed_valid_oos(
    session,
    benchmark_keys: tuple[str, ...] = ("equal_weight_monthly", "csi_300_buy_hold"),
) -> BacktestRun:
    run = BacktestRun(
        id=1,
        strategy_id="demo",
        config_version="wf-000000000000",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        parameters_json="{}",
        started_at=datetime(2026, 1, 1),
        status="success",
    )
    run.benchmarks.extend(
        [BacktestBenchmark(benchmark_key=key, display_name=key) for key in benchmark_keys]
    )
    session.add(run)
    session.flush()
    return run


def test_persistence_helper_validates_and_flushes_parent_and_children_without_commit(
    tmp_path,
) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'persistence.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as session:
        _seed_valid_oos(session)
        run = persist_walk_forward_run(session, run=_input())
        assert run.id > 0
        assert len(run.windows) == 1
        assert session.scalar(select(WalkForwardRun).where(WalkForwardRun.id == run.id)) is not None
        session.rollback()

    with factory() as session:
        assert session.scalar(select(WalkForwardRun)) is None


@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: value.__class__(**{**value.__dict__, "window_count": 2}),
        lambda value: value.__class__(**{**value.__dict__, "windows": ()}),
    ],
)
def test_persistence_helper_rejects_parent_child_drift_before_flush(mutator) -> None:
    value = mutator(_input())
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        with pytest.raises(ValueError):
            persist_walk_forward_run(session, run=value)


def test_persistence_helper_rejects_foreign_strategy_oos_ownership() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        session.add(
            BacktestRun(
                id=1,
                strategy_id="other",
                config_version="wf-000000000000",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                parameters_json="{}",
                started_at=datetime(2026, 1, 1),
                status="success",
            )
        )
        session.flush()

        with pytest.raises(ValueError, match="OOS ownership"):
            persist_walk_forward_run(session, run=_input())


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("config_version", "wf-wrong"),
        ("start_date", date(2026, 1, 2)),
        ("end_date", date(2026, 12, 30)),
        ("status", "failed"),
    ],
)
def test_persistence_helper_rejects_oos_metadata_drift(field_name: str, value: object) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        oos = _seed_valid_oos(session)
        setattr(oos, field_name, value)

        with pytest.raises(ValueError, match="OOS ownership"):
            persist_walk_forward_run(session, run=_input())


def test_persistence_helper_requires_exactly_the_two_fixed_oos_benchmarks() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        _seed_valid_oos(session, benchmark_keys=("equal_weight_monthly",))

        with pytest.raises(ValueError, match="two fixed benchmarks"):
            persist_walk_forward_run(session, run=_input())
