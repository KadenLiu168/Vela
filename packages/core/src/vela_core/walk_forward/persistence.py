from __future__ import annotations

import re
import secrets
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import and_, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
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
HEARTBEAT_INTERVAL_SECONDS = 15
LEASE_DURATION_SECONDS = 120
MAX_ATTEMPTS = 3
MAX_ERROR_MESSAGE_LENGTH = 1024


@dataclass(frozen=True)
class WalkForwardClaim:
    run_id: int
    worker_id: str
    claim_token: str
    attempt_count: int
    claimed_at: datetime
    lease_expires_at: datetime


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


def enqueue_walk_forward_run(
    session: Session,
    *,
    strategy_id: str,
    start_date: date,
    end_date: date,
    walk_forward_config: dict[str, Any],
    base_strategy_config: dict[str, Any],
    config_checksum: str,
    input_data_snapshot: dict[str, Any],
    input_data_checksum: str,
    started_at: datetime,
) -> int:
    _validate_checksum(config_checksum, "config_checksum")
    _validate_checksum(input_data_checksum, "input_data_checksum")
    validate_input_manifest(PROVENANCE_VERSION, input_data_snapshot)
    parent = WalkForwardRun(
        strategy_id=strategy_id,
        start_date=start_date,
        end_date=end_date,
        window_count=0,
        walk_forward_config_json=walk_forward_config,
        base_strategy_config_json=base_strategy_config,
        provenance_version=PROVENANCE_VERSION,
        config_checksum=config_checksum,
        input_data_snapshot_json=input_data_snapshot,
        input_data_checksum=input_data_checksum,
        evidence_version=EVIDENCE_VERSION_V3,
        evidence_json={},
        status="queued",
        attempt_count=0,
        started_at=started_at,
        finished_at=None,
    )
    session.add(parent)
    session.flush()
    session.commit()
    return parent.id


def claim_walk_forward_run(
    session: Session,
    *,
    worker_id: str,
    now: datetime,
    run_id: int | None = None,
    lease_duration_seconds: int = LEASE_DURATION_SECONDS,
    max_attempts: int = MAX_ATTEMPTS,
) -> WalkForwardClaim | None:
    candidate_query = (
        select(WalkForwardRun)
        .where(
            or_(
                WalkForwardRun.status == "queued",
                and_(
                    WalkForwardRun.status == "running",
                    WalkForwardRun.lease_expires_at < now,
                ),
            )
        )
        .where(WalkForwardRun.attempt_count < max_attempts)
        .order_by(WalkForwardRun.created_at.asc(), WalkForwardRun.id.asc())
        .limit(1)
    )
    if run_id is not None:
        candidate_query = candidate_query.where(WalkForwardRun.id == run_id)
    candidate = session.scalar(candidate_query)
    if candidate is None:
        return None

    token = secrets.token_hex(32)
    attempt_count = candidate.attempt_count + 1
    lease_expires_at = now + timedelta(seconds=lease_duration_seconds)
    eligible = or_(
        WalkForwardRun.status == "queued",
        and_(
            WalkForwardRun.status == "running",
            WalkForwardRun.lease_expires_at < now,
        ),
    )
    result = cast(
        CursorResult[Any],
        session.execute(
            update(WalkForwardRun)
            .where(WalkForwardRun.id == candidate.id)
            .where(eligible)
            .where(WalkForwardRun.attempt_count < max_attempts)
            .values(
                status="running",
                attempt_count=WalkForwardRun.attempt_count + 1,
                claimed_at=now,
                heartbeat_at=now,
                lease_expires_at=lease_expires_at,
                worker_id=worker_id,
                claim_token=token,
                finished_at=None,
                error_message=None,
            )
        ),
    )
    if result.rowcount != 1:
        session.rollback()
        return None
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return None
    return WalkForwardClaim(
        run_id=candidate.id,
        worker_id=worker_id,
        claim_token=token,
        attempt_count=attempt_count,
        claimed_at=now,
        lease_expires_at=lease_expires_at,
    )


def heartbeat_walk_forward_run(
    session: Session,
    *,
    run_id: int,
    claim_token: str,
    now: datetime,
    lease_duration_seconds: int = LEASE_DURATION_SECONDS,
) -> bool:
    result = cast(
        CursorResult[Any],
        session.execute(
            update(WalkForwardRun)
            .where(WalkForwardRun.id == run_id)
            .where(WalkForwardRun.status == "running")
            .where(WalkForwardRun.claim_token == claim_token)
            .values(
                heartbeat_at=now,
                lease_expires_at=now + timedelta(seconds=lease_duration_seconds),
            )
        ),
    )
    session.commit()
    return result.rowcount == 1


def transition_walk_forward_run(
    session: Session,
    *,
    run_id: int,
    claim_token: str,
    status: str,
    finished_at: datetime,
    error_message: str | None = None,
    window_count: int | None = None,
    evidence_json: dict[str, Any] | None = None,
    commit: bool = True,
) -> bool:
    if status not in {"success", "failed"}:
        raise ValueError("Walk-forward terminal status must be success or failed")
    values: dict[str, object] = {
        "status": status,
        "error_message": _bound_error_message(error_message),
        "finished_at": finished_at,
    }
    if window_count is not None:
        values["window_count"] = window_count
    if evidence_json is not None:
        values["evidence_json"] = evidence_json
    result = cast(
        CursorResult[Any],
        session.execute(
            update(WalkForwardRun)
            .where(WalkForwardRun.id == run_id)
            .where(WalkForwardRun.status == "running")
            .where(WalkForwardRun.claim_token == claim_token)
            .values(**values)
        ),
    )
    if commit:
        session.commit()
    return result.rowcount == 1


def mark_expired_walk_forward_runs_failed(
    session: Session,
    *,
    now: datetime,
    max_attempts: int = MAX_ATTEMPTS,
) -> int:
    result = cast(
        CursorResult[Any],
        session.execute(
            update(WalkForwardRun)
            .where(WalkForwardRun.status == "running")
            .where(WalkForwardRun.lease_expires_at < now)
            .where(WalkForwardRun.attempt_count >= max_attempts)
            .values(
                status="failed",
                finished_at=now,
                error_message="worker_lost: maximum durable attempts exhausted",
            )
        ),
    )
    session.commit()
    return result.rowcount


def persist_walk_forward_run(
    session: Session, *, run: WalkForwardPersistenceInput, run_id: int | None = None
) -> WalkForwardRun:
    """Persist ordered window children.

    With ``run_id=None`` this retains the historical persistence helper for
    existing callers. Durable execution uses an already enqueued parent id and
    performs its fenced terminal transition separately.
    """
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
    if run_id is None:
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
            status="success",
            started_at=run.started_at,
            finished_at=run.finished_at,
        )
        session.add(parent)
    else:
        existing = session.get(WalkForwardRun, run_id)
        if existing is None:
            raise PersistedDataContractError(f"WalkForwardRun {run_id} does not exist")
        parent = existing
    parent.windows.extend(children)
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


def _bound_error_message(value: str | None) -> str | None:
    if value is None:
        return None
    return value[:MAX_ERROR_MESSAGE_LENGTH]


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
