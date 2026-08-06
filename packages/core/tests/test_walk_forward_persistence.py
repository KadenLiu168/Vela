from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from vela_core.models import BacktestBenchmark, BacktestRun, Base, WalkForwardRun
from vela_core.walk_forward.evidence import PersistedDataContractError
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


def _regime_summary(value: float | None) -> dict[str, object]:
    return {
        "mean": value,
        "median": value,
        "min": value,
        "max": value,
        "std": 0.0 if value is not None else None,
        "window_count": 1,
        "valid_count": 1 if value is not None else 0,
        "evidence_status": "insufficient_evidence",
    }


def _tail_owner(
    *,
    var: float | None,
    cvar: float | None,
    skew: float | None,
    kurt: float | None,
    observations: int = 100,
) -> dict[str, object]:
    return {
        "historical_var_95": var,
        "historical_cvar_95": cvar,
        "return_skewness": skew,
        "return_excess_kurtosis": kurt,
        "observation_count": observations,
        "tail_observation_count": 5,
        "evidence_status": "sufficient" if observations >= 100 else "insufficient_evidence",
    }


def _tail_agg(value: float | None) -> dict[str, object]:
    if value is None:
        return {
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "std": None,
            "window_count": 1,
            "valid_count": 0,
            "evidence_status": "insufficient_evidence",
        }
    return {
        "mean": value,
        "median": value,
        "min": value,
        "max": value,
        "std": 0.0,
        "window_count": 1,
        "valid_count": 1,
        "evidence_status": "insufficient_evidence",
    }


def _tail_evidence() -> dict[str, object]:
    owners = {
        "strategy": _tail_owner(var=0.02, cvar=0.06, skew=0.1, kurt=0.2),
        "equal_weight_monthly": _tail_owner(var=0.01, cvar=0.03, skew=-0.1, kurt=0.1),
        "csi_300_buy_hold": _tail_owner(var=0.04, cvar=0.08, skew=0.2, kurt=-0.3),
    }
    metrics = (
        "historical_var_95",
        "historical_cvar_95",
        "return_skewness",
        "return_excess_kurtosis",
    )
    aggregates = {
        owner: {metric: _tail_agg(values[metric]) for metric in metrics}
        for owner, values in owners.items()
    }
    return {
        "per_window": [{"ordinal": 0, "owners": deepcopy(owners)}],
        "aggregates": aggregates,
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
    csi_comparison = {
        "total_return_difference": _summary(),
        "annualized_return_difference": _summary(),
        "tracking_error": _summary(),
        "information_ratio": _summary(),
        "outperformance_rate": rate,
        "capm_alpha": _regime_summary(0.1),
        "capm_beta": _regime_summary(0.1),
        "capm_r_squared": _regime_summary(0.1),
        "up_capture_ratio": _regime_summary(0.1),
        "down_capture_ratio": _regime_summary(0.1),
    }
    equal_weight_comparison = {
        **csi_comparison,
        "capm_alpha": _regime_summary(None),
        "capm_beta": _regime_summary(None),
        "capm_r_squared": _regime_summary(None),
    }
    return {
        "metrics": metrics,
        "positive_window_rate": rate,
        "generalization_gap": _summary(),
        "benchmarks": {
            "equal_weight_monthly": equal_weight_comparison,
            "csi_300_buy_hold": csi_comparison,
        },
        "parameter_stability": {},
        "tail_distribution": _tail_evidence(),
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
        parameters_json=(
            '{"benchmark_regime_metric_version":"benchmark_regime_metrics_v1",'
            '"tail_distribution_metric_version":"tail_distribution_metrics_v1"}'
        ),
        started_at=datetime(2026, 1, 1),
        status="success",
        historical_var_95=Decimal("0.02"),
        historical_cvar_95=Decimal("0.06"),
        return_skewness=Decimal("0.1"),
        return_excess_kurtosis=Decimal("0.2"),
        distribution_observation_count=100,
        tail_observation_count=5,
    )
    benchmark_values = {
        "equal_weight_monthly": (0.01, 0.03, -0.1, 0.1),
        "csi_300_buy_hold": (0.04, 0.08, 0.2, -0.3),
    }
    run.benchmarks.extend(
        [
            BacktestBenchmark(
                benchmark_key=key,
                display_name=key,
                capm_alpha=Decimal("0.1") if key == "csi_300_buy_hold" else None,
                capm_beta=Decimal("0.1") if key == "csi_300_buy_hold" else None,
                capm_r_squared=Decimal("0.1") if key == "csi_300_buy_hold" else None,
                capm_observation_count=2 if key == "csi_300_buy_hold" else None,
                up_capture_ratio=Decimal("0.1"),
                up_capture_observation_count=1,
                down_capture_ratio=Decimal("0.1"),
                down_capture_observation_count=1,
                historical_var_95=Decimal(str(benchmark_values[key][0])),
                historical_cvar_95=Decimal(str(benchmark_values[key][1])),
                return_skewness=Decimal(str(benchmark_values[key][2])),
                return_excess_kurtosis=Decimal(str(benchmark_values[key][3])),
                distribution_observation_count=100,
                tail_observation_count=5,
            )
            for key in benchmark_keys
        ]
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


def test_persistence_helper_rejects_regime_evidence_that_mismatches_source_rows() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        _seed_valid_oos(session)
        value = _input()
        evidence = deepcopy(value.evidence)
        evidence["benchmarks"]["csi_300_buy_hold"]["capm_alpha"].update(
            {"mean": 999.0, "median": 999.0, "min": 999.0, "max": 999.0, "std": 0.0}
        )
        corrupt = value.__class__(**{**value.__dict__, "evidence": evidence})

        with pytest.raises(PersistedDataContractError, match="source OOS rows"):
            persist_walk_forward_run(session, run=corrupt)


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
