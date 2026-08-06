from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.models import BacktestRun, WalkForwardRun, WalkForwardRunWindow
from vela_core.walk_forward.candidate_audit import build_candidate_audit
from vela_core.walk_forward.evidence import (
    EVIDENCE_VERSION_V3,
    PersistedDataContractError,
    WalkForwardEvidenceV3,
    validate_wf_evidence,
)
from vela_core.walk_forward.provenance import PROVENANCE_VERSION, validate_input_manifest
from vela_core.walk_forward.regime_evidence_validation import (
    validate_v2_regime_source_evidence,
)
from vela_core.walk_forward.tail_evidence_validation import (
    validate_v3_tail_source_evidence,
)

_CHECKSUM = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class WalkForwardWindowPersistenceInput:
    ordinal: int
    train_start: date
    train_end: date
    test_start: date
    test_end: date
    oos_version: str
    selected_parameters: dict[str, Any]
    candidate_count: int
    eligible_count: int
    skipped_count: int
    skip_reason_counts: dict[str, int]
    train_sharpe: Decimal | float | int | None
    oos_backtest_run_id: int


@dataclass(frozen=True)
class WalkForwardPersistenceInput:
    strategy_id: str
    start_date: date
    end_date: date
    window_count: int
    walk_forward_config: dict[str, Any]
    base_strategy_config: dict[str, Any]
    config_checksum: str
    input_data_snapshot: dict[str, Any]
    input_data_checksum: str
    evidence: dict[str, Any]
    started_at: datetime
    finished_at: datetime
    windows: Sequence[WalkForwardWindowPersistenceInput]


def persist_walk_forward_run(
    session: Session, *, run: WalkForwardPersistenceInput
) -> WalkForwardRun:
    if run.window_count < 0 or run.window_count != len(run.windows):
        raise ValueError("Walk-forward parent window count must equal child count")
    _validate_checksum(run.config_checksum, "config_checksum")
    _validate_checksum(run.input_data_checksum, "input_data_checksum")
    validate_input_manifest(PROVENANCE_VERSION, run.input_data_snapshot)
    evidence = validate_wf_evidence(EVIDENCE_VERSION_V3, run.evidence)
    assert isinstance(evidence, WalkForwardEvidenceV3)
    children = _build_windows(run.windows)
    oos_rows = _validate_oos_ownership(session, run)
    validate_v2_regime_source_evidence(oos_rows, evidence)
    validate_v3_tail_source_evidence(oos_rows, evidence)
    if len(children) != run.window_count:
        raise ValueError("Walk-forward parent window count must equal child count")
    parent = WalkForwardRun(
        strategy_id=run.strategy_id,
        start_date=run.start_date,
        end_date=run.end_date,
        window_count=run.window_count,
        walk_forward_config_json=run.walk_forward_config,
        base_strategy_config_json=run.base_strategy_config,
        provenance_version=PROVENANCE_VERSION,
        config_checksum=run.config_checksum,
        input_data_snapshot_json=run.input_data_snapshot,
        input_data_checksum=run.input_data_checksum,
        evidence_version=EVIDENCE_VERSION_V3,
        evidence_json=evidence.model_dump(mode="json"),
        started_at=run.started_at,
        finished_at=run.finished_at,
    )
    parent.windows.extend(children)
    session.add(parent)
    session.flush()
    return parent


def _build_windows(
    values: Sequence[WalkForwardWindowPersistenceInput],
) -> list[WalkForwardRunWindow]:
    result: list[WalkForwardRunWindow] = []
    seen_oos_ids: set[int] = set()
    for expected_ordinal, value in enumerate(values):
        if value.ordinal != expected_ordinal:
            raise ValueError("Walk-forward windows must have contiguous chronological ordinals")
        if value.oos_backtest_run_id in seen_oos_ids:
            raise ValueError("Walk-forward OOS backtest ownership must be unique")
        seen_oos_ids.add(value.oos_backtest_run_id)
        audit = build_candidate_audit(
            candidate_count=value.candidate_count,
            eligible_count=value.eligible_count,
            reason_counts=value.skip_reason_counts,
        )
        if audit["skipped_count"] != value.skipped_count:
            raise ValueError("Walk-forward skipped count must reconcile with reason counts")
        result.append(
            WalkForwardRunWindow(
                ordinal=value.ordinal,
                train_start=value.train_start,
                train_end=value.train_end,
                test_start=value.test_start,
                test_end=value.test_end,
                oos_version=value.oos_version,
                selected_parameters_json=value.selected_parameters,
                candidate_count=audit["candidate_count"],
                eligible_count=audit["eligible_count"],
                skipped_count=audit["skipped_count"],
                skip_reason_counts_json=audit["skip_reason_counts"],
                train_sharpe=value.train_sharpe,
                oos_backtest_run_id=value.oos_backtest_run_id,
            )
        )
    return result


def _validate_checksum(value: str, field_name: str) -> None:
    if _CHECKSUM.fullmatch(value) is None:
        raise PersistedDataContractError(f"{field_name} must be a lowercase SHA-256 checksum")


def _validate_oos_ownership(
    session: Session, run: WalkForwardPersistenceInput
) -> list[BacktestRun]:
    expected_benchmarks = {"equal_weight_monthly", "csi_300_buy_hold"}
    oos_rows = {
        row.id: row
        for row in session.scalars(
            select(BacktestRun).where(
                BacktestRun.id.in_(window.oos_backtest_run_id for window in run.windows)
            )
        )
    }
    ordered_rows: list[BacktestRun] = []
    for window in run.windows:
        oos = oos_rows.get(window.oos_backtest_run_id)
        if (
            oos is None
            or oos.strategy_id != run.strategy_id
            or oos.config_version != window.oos_version
            or oos.start_date != window.test_start
            or oos.end_date != window.test_end
            or oos.status != "success"
        ):
            raise ValueError("Walk-forward OOS ownership does not match the persisted window")
        benchmark_keys = [benchmark.benchmark_key for benchmark in oos.benchmarks]
        if len(benchmark_keys) != 2 or set(benchmark_keys) != expected_benchmarks:
            raise ValueError("Walk-forward OOS ownership requires exactly the two fixed benchmarks")
        ordered_rows.append(oos)
    return ordered_rows
