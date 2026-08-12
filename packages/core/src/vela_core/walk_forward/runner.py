from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vela_core.backtest_runner import run_backtest
from vela_core.models import WalkForwardRun
from vela_core.strategy_config import validate_strategy_config
from vela_core.walk_forward.config import WalkForwardConfig
from vela_core.walk_forward.evidence import WalkForwardEvidenceV3
from vela_core.walk_forward.parameter_space import (
    build_strategy_config,
    canonical_combination,
    generate_combinations,
)
from vela_core.walk_forward.persistence import (
    WalkForwardPersistenceInput,
    WalkForwardWindowPersistenceInput,
    claim_walk_forward_run,
    enqueue_walk_forward_run,
    persist_walk_forward_run,
    transition_walk_forward_run,
)
from vela_core.walk_forward.preflight import WalkForwardPreflight, prepare_walk_forward_inputs
from vela_core.walk_forward.provenance import (
    canonical_provenance_bytes,
    canonical_provenance_payload,
    sha256_hex,
)
from vela_core.walk_forward.report import (
    WalkForwardBenchmarkResult,
    WalkForwardReport,
    WalkForwardWindowResult,
)
from vela_core.walk_forward.window_splitter import WalkForwardWindow

logger = logging.getLogger(__name__)


class LostWalkForwardClaim(RuntimeError):
    """Raised when a worker no longer owns the durable Walk-forward parent."""


def _policy_version(manifest: dict[str, object]) -> str | None:
    value = manifest.get("resolution_policy_version")
    return value if isinstance(value, str) else None


class WalkForwardRunner:
    def __init__(
        self,
        config: WalkForwardConfig,
        *,
        base_strategy_config: dict[str, Any] | None = None,
    ) -> None:
        self.config = config
        self._base_config = (
            base_strategy_config
            if base_strategy_config is not None
            else _load_base_config(config.strategy.base_config)
        )
        self._base_strategy_config = validate_strategy_config(self._base_config)
        self._version_contents: dict[str, str] = {}

    @classmethod
    def from_persisted(cls, parent: WalkForwardRun) -> WalkForwardRunner:
        return cls(
            WalkForwardConfig.model_validate(parent.walk_forward_config_json),
            base_strategy_config=parent.base_strategy_config_json,
        )

    def run(self, session: Session) -> WalkForwardReport:
        run_id = self.enqueue(session)
        claim = claim_walk_forward_run(
            session,
            worker_id=f"sync-cli:{uuid4().hex}",
            now=datetime.now(UTC),
            run_id=run_id,
        )
        if claim is None:
            raise RuntimeError("walk-forward claim could not be acquired")
        return self.complete(session, run_id, claim.claim_token)

    def enqueue(self, session: Session) -> int:
        """Preflight and commit a durable queued parent row."""
        self._require_sqlite(session)
        started_at = datetime.now(UTC)
        prepared = prepare_walk_forward_inputs(
            session,
            config=self.config,
            base_config=self._base_config,
        )
        return self._persist_queued(session, prepared=prepared, started_at=started_at)

    def begin(self, session: Session) -> tuple[int, datetime]:
        """Compatibility wrapper for callers that only need enqueue identity."""
        run_id = self.enqueue(session)
        parent = session.get(WalkForwardRun, run_id)
        if parent is None:
            raise RuntimeError(f"WalkForwardRun {run_id} disappeared after enqueue")
        return run_id, parent.started_at

    def complete(self, session: Session, run_id: int, claim_token: str) -> WalkForwardReport:
        """Execute and publish one existing parent under a fenced claim."""
        self._require_sqlite(session)
        parent = session.get(WalkForwardRun, run_id)
        if parent is None or parent.status != "running" or parent.claim_token != claim_token:
            raise LostWalkForwardClaim(f"Walk-forward claim {run_id} is no longer owned")
        started_at = parent.started_at
        try:
            prepared = prepare_walk_forward_inputs(
                session,
                config=self.config,
                base_config=self._base_config,
            )
            self._validate_persisted_input(parent, prepared)
            windows = prepared.windows
            combinations = generate_combinations(self.config.parameter_space)
            with _memory_snapshot(session) as memory:
                results = [
                    self._run_window(session, memory, item, combinations) for item in windows
                ]
            report = WalkForwardReport(results)
            oos_ids = [_require_oos_id(item.oos_backtest_id) for item in results]
            evidence = report.evidence_document()
            finished_at = datetime.now(UTC)
            self._persist_success(
                session,
                run_id=run_id,
                results=results,
                oos_ids=oos_ids,
                evidence=evidence,
                started_at=started_at,
                finished_at=finished_at,
                parent=parent,
            )
            if not transition_walk_forward_run(
                session,
                run_id=run_id,
                claim_token=claim_token,
                status="success",
                finished_at=finished_at,
                window_count=len(results),
                evidence_json=evidence.model_dump(mode="json"),
                commit=False,
            ):
                raise LostWalkForwardClaim(f"Walk-forward claim {run_id} was fenced")
            session.commit()
            report.walk_forward_run_id = run_id
            return report
        except LostWalkForwardClaim:
            session.rollback()
            raise
        except Exception as exc:
            # Discard any OOS/signal/curve/benchmark rows produced by this
            # attempt, then record failure only if this claim still owns it.
            session.rollback()
            if not transition_walk_forward_run(
                session,
                run_id=run_id,
                claim_token=claim_token,
                status="failed",
                error_message=str(exc),
                finished_at=datetime.now(UTC),
            ):
                session.rollback()
                raise LostWalkForwardClaim(f"Walk-forward claim {run_id} was fenced") from exc
            raise

    def _persist_queued(
        self,
        session: Session,
        *,
        prepared: WalkForwardPreflight,
        started_at: datetime,
    ) -> int:
        walk_forward_snapshot = self.config.model_dump(mode="json")
        base_strategy_snapshot = self._base_strategy_config.model_dump(mode="json")
        provenance_payload = canonical_provenance_payload(
            walk_forward_snapshot,
            base_strategy_snapshot,
            version=str(prepared.manifest["version"]),
            resolution_policy_version=_policy_version(prepared.manifest),
        )
        return enqueue_walk_forward_run(
            session,
            strategy_id=self._base_strategy_config.strategy_id,
            start_date=self.config.window.start_date,
            end_date=self.config.window.end_date,
            walk_forward_config=walk_forward_snapshot,
            base_strategy_config=base_strategy_snapshot,
            config_checksum=sha256_hex(canonical_provenance_bytes(provenance_payload)),
            input_data_snapshot=prepared.manifest,
            input_data_checksum=prepared.input_data_checksum,
            started_at=started_at,
        )

    @staticmethod
    def _require_sqlite(session: Session) -> None:
        if session.get_bind().dialect.name != "sqlite":
            raise ValueError("walk-forward only supports SQLite source databases")

    def _validate_persisted_input(
        self, parent: WalkForwardRun, prepared: WalkForwardPreflight
    ) -> None:
        walk_forward_snapshot = self.config.model_dump(mode="json")
        base_strategy_snapshot = self._base_strategy_config.model_dump(mode="json")
        provenance_payload = canonical_provenance_payload(
            walk_forward_snapshot,
            base_strategy_snapshot,
            version=str(prepared.manifest["version"]),
            resolution_policy_version=_policy_version(prepared.manifest),
        )
        if (
            parent.strategy_id != self._base_strategy_config.strategy_id
            or parent.start_date != self.config.window.start_date
            or parent.end_date != self.config.window.end_date
            or parent.config_checksum != sha256_hex(canonical_provenance_bytes(provenance_payload))
            or parent.input_data_checksum != prepared.input_data_checksum
            or parent.input_data_snapshot_json != prepared.manifest
        ):
            raise ValueError("walk-forward input provenance drift detected")

    def _persist_success(
        self,
        session: Session,
        *,
        run_id: int,
        results: list[WalkForwardWindowResult],
        oos_ids: list[int],
        evidence: WalkForwardEvidenceV3,
        started_at: datetime,
        finished_at: datetime,
        parent: WalkForwardRun,
    ) -> None:
        persist_walk_forward_run(
            session,
            run_id=run_id,
            run=WalkForwardPersistenceInput(
                strategy_id=self._base_strategy_config.strategy_id,
                start_date=self.config.window.start_date,
                end_date=self.config.window.end_date,
                window_count=len(results),
                walk_forward_config=parent.walk_forward_config_json,
                base_strategy_config=parent.base_strategy_config_json,
                config_checksum=parent.config_checksum,
                input_data_snapshot=parent.input_data_snapshot_json,
                input_data_checksum=parent.input_data_checksum,
                evidence=evidence.model_dump(mode="json"),
                started_at=started_at,
                finished_at=finished_at,
                windows=tuple(
                    WalkForwardWindowPersistenceInput(
                        ordinal=index,
                        train_start=item.window.train_start,
                        train_end=item.window.train_end,
                        test_start=item.window.test_start,
                        test_end=item.window.test_end,
                        oos_version=item.oos_version,
                        selected_parameters=item.best_combo,
                        candidate_count=item.candidate_count,
                        eligible_count=item.eligible_count,
                        skipped_count=item.skipped_count,
                        skip_reason_counts=item.skip_reason_counts,
                        train_sharpe=item.train_sharpe,
                        oos_backtest_run_id=oos_id,
                    )
                    for index, (item, oos_id) in enumerate(zip(results, oos_ids, strict=True))
                ),
            ),
        )

    def _run_window(
        self,
        source: Session,
        memory: Session,
        window: WalkForwardWindow,
        combinations: list[dict[str, Any]],
    ) -> WalkForwardWindowResult:
        scored: list[tuple[float, str, dict[str, Any], Any]] = []
        skipped: list[str] = []
        skip_reason_counts: dict[str, int] = {}
        for combo in combinations:
            built = build_strategy_config(self._base_config, combo)
            if built.config is None:
                memory.rollback()
                reason = f"{canonical_combination(combo)}: {built.skip_reason}"
                logger.warning("Walk-forward skipped combination %s", reason)
                skipped.append(reason)
                skip_reason_counts["invalid_config"] = (
                    skip_reason_counts.get("invalid_config", 0) + 1
                )
                continue
            try:
                result = run_backtest(
                    memory,
                    config=built.config,
                    start_date=window.train_start,
                    end_date=window.train_end,
                    calculate_benchmarks=False,
                )
                if result.status == "success" and result.sharpe_ratio is not None:
                    scored.append(
                        (
                            float(result.sharpe_ratio),
                            canonical_combination(combo),
                            combo,
                            built.config,
                        )
                    )
                    memory.commit()
                else:
                    memory.rollback()
                    reason = f"{canonical_combination(combo)}: unscorable result"
                    logger.warning("Walk-forward skipped combination %s", reason)
                    skipped.append(reason)
                    category = (
                        "missing_train_sharpe"
                        if result.status == "success"
                        else "training_non_success"
                    )
                    skip_reason_counts[category] = skip_reason_counts.get(category, 0) + 1
            except Exception as exc:
                memory.rollback()
                reason = f"{canonical_combination(combo)}: {exc}"
                logger.warning("Walk-forward skipped combination %s", reason)
                skipped.append(reason)
                skip_reason_counts["training_error"] = (
                    skip_reason_counts.get("training_error", 0) + 1
                )
        if not scored:
            raise RuntimeError("no scorable parameter combinations before OOS evaluation")
        best = min(scored, key=lambda item: (-item[0], item[1]))
        validated_data = best[3].model_dump(mode="json")
        selected_parameters = _validated_combination(validated_data, best[2])
        version = _version_for_config(validated_data)
        content = _canonical_config_content(validated_data)
        if self._version_contents.get(version) not in (None, content):
            raise RuntimeError(f"walk-forward version collision for {version}")
        self._version_contents[version] = content
        oos_config = best[3].model_copy(update={"version": version})
        oos = run_backtest(
            source,
            config=oos_config,
            start_date=window.test_start,
            end_date=window.test_end,
            calculate_benchmarks=True,
        )
        if oos.status != "success":
            raise RuntimeError(f"OOS backtest returned {oos.status}")
        return WalkForwardWindowResult(
            window=window,
            best_combo=selected_parameters,
            oos_version=version,
            train_sharpe=best[0],
            oos_total_return=_number(oos.total_return),
            oos_annualized_return=_number(oos.annualized_return),
            oos_sharpe=_number(oos.sharpe_ratio),
            oos_max_drawdown=_number(oos.max_drawdown),
            oos_volatility=_number(oos.volatility),
            oos_sortino=_number(getattr(oos, "sortino_ratio", None)),
            oos_calmar=_number(getattr(oos, "calmar_ratio", None)),
            oos_longest_drawdown_duration_sessions=getattr(
                oos, "longest_drawdown_duration_sessions", None
            ),
            historical_var_95=_number(getattr(oos, "historical_var_95", None)),
            historical_cvar_95=_number(getattr(oos, "historical_cvar_95", None)),
            return_skewness=_number(getattr(oos, "return_skewness", None)),
            return_excess_kurtosis=_number(getattr(oos, "return_excess_kurtosis", None)),
            distribution_observation_count=getattr(oos, "distribution_observation_count", None),
            tail_observation_count=getattr(oos, "tail_observation_count", None),
            benchmarks=tuple(
                WalkForwardBenchmarkResult(
                    key=item.key,
                    name=item.name,
                    total_return=_number(item.annualized_return.total_return),
                    annualized_return=_number(item.annualized_return.annualized_return),
                    max_drawdown=_number(item.maximum_drawdown.max_drawdown),
                    volatility=_number(item.volatility.volatility),
                    sharpe_ratio=_number(item.sharpe_ratio.sharpe_ratio),
                    total_return_difference=_difference(
                        oos.total_return, item.annualized_return.total_return
                    ),
                    annualized_return_difference=_difference(
                        oos.annualized_return, item.annualized_return.annualized_return
                    ),
                    tracking_error=_number(getattr(item, "tracking_error", None)),
                    information_ratio=_number(getattr(item, "information_ratio", None)),
                    capm_alpha=_number(getattr(item, "capm_alpha", None)),
                    capm_beta=_number(getattr(item, "capm_beta", None)),
                    capm_r_squared=_number(getattr(item, "capm_r_squared", None)),
                    capm_observation_count=getattr(item, "capm_observation_count", None),
                    up_capture_ratio=_number(getattr(item, "up_capture_ratio", None)),
                    up_capture_observation_count=getattr(
                        item, "up_capture_observation_count", None
                    ),
                    down_capture_ratio=_number(getattr(item, "down_capture_ratio", None)),
                    down_capture_observation_count=getattr(
                        item, "down_capture_observation_count", None
                    ),
                    historical_var_95=_number(getattr(item, "historical_var_95", None)),
                    historical_cvar_95=_number(getattr(item, "historical_cvar_95", None)),
                    return_skewness=_number(getattr(item, "return_skewness", None)),
                    return_excess_kurtosis=_number(getattr(item, "return_excess_kurtosis", None)),
                    distribution_observation_count=getattr(
                        item, "distribution_observation_count", None
                    ),
                    tail_observation_count=getattr(item, "tail_observation_count", None),
                )
                for item in getattr(oos, "benchmarks", ())
            ),
            skipped=skipped,
            oos_backtest_id=getattr(oos, "backtest_run_id", None),
            candidate_count=len(combinations),
            eligible_count=len(scored),
            skipped_count=len(combinations) - len(scored),
            skip_reason_counts=skip_reason_counts,
        )


def _load_base_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError(f"base strategy configuration {path} must be a mapping")
    return data


@contextmanager
def _memory_snapshot(source: Session) -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", poolclass=StaticPool)
    source_connection = source.connection().connection.dbapi_connection
    with engine.connect() as target:
        target_connection = target.connection.dbapi_connection
        if source_connection is None or target_connection is None:
            raise RuntimeError("SQLite backup connection is unavailable")
        source_connection.backup(target_connection)
    memory = sessionmaker(bind=engine)()
    try:
        yield memory
    finally:
        memory.close()
        engine.dispose()


def _version_for_config(data: dict[str, Any]) -> str:
    return "wf-" + hashlib.sha256(_canonical_config_content(data).encode()).hexdigest()[:12]


def _canonical_config_content(data: dict[str, Any]) -> str:
    content = dict(data)
    content.pop("version", None)
    return json.dumps(content, sort_keys=True, separators=(",", ":"))


def _validated_combination(
    validated_config: dict[str, Any], combination: dict[str, Any]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for path in combination:
        value: Any = validated_config
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                raise RuntimeError(f"validated strategy configuration is missing {path}")
            value = value[part]
        result[path] = value
    return result


def _number(value: Decimal | float | int | None) -> float | None:
    return None if value is None else float(value)


def _difference(left: Decimal | float | None, right: Decimal | float | None) -> float | None:
    return None if left is None or right is None else float(left) - float(right)


def _require_oos_id(value: int | None) -> int:
    if value is None:
        raise RuntimeError("successful OOS backtest did not return a persisted id")
    return value
