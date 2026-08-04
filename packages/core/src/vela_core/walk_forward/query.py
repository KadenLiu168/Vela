from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from vela_core.models import BacktestRun, WalkForwardRun, WalkForwardRunWindow
from vela_core.walk_forward.candidate_audit import build_candidate_audit
from vela_core.walk_forward.evidence import (
    PersistedDataContractError,
    validate_wf_evidence,
)
from vela_core.walk_forward.provenance import validate_input_manifest


def list_walk_forward_runs(
    session: Session, *, strategy_id: str, limit: int, offset: int = 0
) -> tuple[list[WalkForwardRun], int]:
    _validate_pagination(limit, offset)
    total = session.scalar(
        select(func.count())
        .select_from(WalkForwardRun)
        .where(WalkForwardRun.strategy_id == strategy_id)
    )
    rows = list(
        session.scalars(
            select(WalkForwardRun)
            .where(WalkForwardRun.strategy_id == strategy_id)
            .order_by(WalkForwardRun.finished_at.desc(), WalkForwardRun.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    )
    for row in rows:
        validate_walk_forward_run(row)
    return rows, int(total or 0)


def get_walk_forward_run(
    session: Session, *, run_id: int, strategy_id: str
) -> WalkForwardRun | None:
    row = session.scalar(
        select(WalkForwardRun)
        .options(
            selectinload(WalkForwardRun.windows)
            .selectinload(WalkForwardRunWindow.oos_backtest_run)
            .selectinload(BacktestRun.benchmarks)
        )
        .where(WalkForwardRun.id == run_id)
        .where(WalkForwardRun.strategy_id == strategy_id)
    )
    if row is None:
        return None
    validate_walk_forward_run(row)
    return row


def validate_walk_forward_run(row: WalkForwardRun) -> None:
    if row.provenance_version != "wf_provenance_v1":
        raise PersistedDataContractError(
            f"unsupported Walk-forward provenance version: {row.provenance_version}"
        )
    validate_input_manifest(row.provenance_version, row.input_data_snapshot_json)
    validate_wf_evidence(row.evidence_version, row.evidence_json)
    if row.window_count != len(row.windows):
        raise PersistedDataContractError("Walk-forward window count does not match children")
    seen_oos: set[int] = set()
    expected_benchmarks = {"equal_weight_monthly", "csi_300_buy_hold"}
    for expected_ordinal, child in enumerate(row.windows):
        if child.ordinal != expected_ordinal:
            raise PersistedDataContractError("Walk-forward child ordinals are not chronological")
        if child.oos_backtest_run_id in seen_oos:
            raise PersistedDataContractError("Walk-forward OOS ownership is not unique")
        seen_oos.add(child.oos_backtest_run_id)
        oos = child.oos_backtest_run
        if (
            oos is None
            or oos.strategy_id != row.strategy_id
            or oos.config_version != child.oos_version
            or oos.start_date != child.test_start
            or oos.end_date != child.test_end
            or oos.status != "success"
        ):
            raise PersistedDataContractError(
                "Walk-forward OOS ownership does not match the persisted window"
            )
        benchmark_keys = [benchmark.benchmark_key for benchmark in oos.benchmarks]
        if len(benchmark_keys) != 2 or set(benchmark_keys) != expected_benchmarks:
            raise PersistedDataContractError(
                "Walk-forward OOS ownership does not contain exactly the two fixed benchmarks"
            )
        try:
            audit = build_candidate_audit(
                candidate_count=child.candidate_count,
                eligible_count=child.eligible_count,
                reason_counts=child.skip_reason_counts_json,
            )
        except ValueError as exc:
            raise PersistedDataContractError("invalid Walk-forward candidate audit") from exc
        if audit["skipped_count"] != child.skipped_count:
            raise PersistedDataContractError("Walk-forward candidate audit is unreconciled")


def _validate_pagination(limit: int, offset: int) -> None:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    if offset < 0:
        raise ValueError("offset must be non-negative")
