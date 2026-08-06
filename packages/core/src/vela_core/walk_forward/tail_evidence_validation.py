from __future__ import annotations

import json
import math
from collections.abc import Sequence
from statistics import mean, median, pstdev

from vela_core.models import BacktestBenchmark, BacktestRun
from vela_core.walk_forward.evidence import (
    TAIL_OWNER_KEYS,
    PersistedDataContractError,
    WalkForwardEvidenceV3,
    WalkForwardMetricSummaryModel,
    WalkForwardTailDistributionOwnerModel,
)

_METRIC_VERSION = "tail_distribution_metrics_v1"
_MINIMUM_PUBLICATION_OBSERVATIONS = 100
_TAIL_METRICS = (
    "historical_var_95",
    "historical_cvar_95",
    "return_skewness",
    "return_excess_kurtosis",
)


def validate_v3_tail_source_evidence(
    oos_rows: Sequence[BacktestRun], evidence: WalkForwardEvidenceV3
) -> None:
    """Validate v3 tail-distribution evidence against its owned source rows.

    Every selected OOS row must record the tail metric version and its
    per-window owner values must match the persisted strategy/benchmark fields
    exactly. Aggregates must reconcile with the per-window values using the
    same descriptive-statistics contract as the other evidence families.
    """
    if len(oos_rows) != len(evidence.tail_distribution.per_window):
        raise PersistedDataContractError(
            "Walk-forward v3 tail evidence window count does not match source OOS rows"
        )
    for ordinal, oos in enumerate(oos_rows):
        _validate_source_version(oos)
        benchmarks = {benchmark.benchmark_key: benchmark for benchmark in oos.benchmarks}
        if set(benchmarks) != {"equal_weight_monthly", "csi_300_buy_hold"}:
            raise PersistedDataContractError(
                "Walk-forward v3 source OOS rows require exactly the two fixed benchmarks"
            )
        window = evidence.tail_distribution.per_window[ordinal]
        if window.ordinal != ordinal:
            raise PersistedDataContractError(
                "Walk-forward v3 tail window ordinals are not chronological"
            )
        _validate_owner(
            window.owners["strategy"],
            oos,
            owner_label=f"window {ordinal} strategy",
        )
        for benchmark_key, benchmark in benchmarks.items():
            _validate_owner(
                window.owners[benchmark_key],
                benchmark,
                owner_label=f"window {ordinal} {benchmark_key}",
            )

    for owner in TAIL_OWNER_KEYS:
        for metric in _TAIL_METRICS:
            values = [
                getattr(window.owners[owner], metric)
                for window in evidence.tail_distribution.per_window
            ]
            _validate_summary(
                getattr(evidence.tail_distribution.aggregates[owner], metric),
                values,
                window_count=len(oos_rows),
                owner_label=f"{owner}.{metric}",
            )


def _validate_source_version(oos: BacktestRun) -> None:
    try:
        parameters = json.loads(oos.parameters_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise PersistedDataContractError(
            "Walk-forward v3 source OOS parameters are invalid"
        ) from exc
    if (
        not isinstance(parameters, dict)
        or parameters.get("tail_distribution_metric_version") != _METRIC_VERSION
    ):
        raise PersistedDataContractError("Walk-forward v3 source OOS metric version is invalid")


def _validate_owner(
    owner: WalkForwardTailDistributionOwnerModel,
    source: BacktestRun | BacktestBenchmark,
    *,
    owner_label: str,
) -> None:
    observation_count = getattr(source, "distribution_observation_count", None)
    tail_observation_count = getattr(source, "tail_observation_count", None)
    if type(observation_count) is not int or observation_count < 0:
        raise PersistedDataContractError(
            f"Walk-forward v3 {owner_label} observation count is invalid"
        )
    if type(tail_observation_count) is not int or tail_observation_count < 0:
        raise PersistedDataContractError(f"Walk-forward v3 {owner_label} tail count is invalid")
    expected_tail_count = math.ceil(0.05 * observation_count)
    if tail_observation_count != expected_tail_count:
        raise PersistedDataContractError(
            f"Walk-forward v3 {owner_label} tail count does not match the rank rule"
        )
    expected_status = (
        "sufficient"
        if observation_count >= _MINIMUM_PUBLICATION_OBSERVATIONS
        else "insufficient_evidence"
    )
    if owner.evidence_status != expected_status:
        raise PersistedDataContractError(
            f"Walk-forward v3 {owner_label} evidence status does not match its count"
        )
    if observation_count != owner.observation_count:
        raise PersistedDataContractError(
            f"Walk-forward v3 {owner_label} observation count does not match its source"
        )
    if tail_observation_count != owner.tail_observation_count:
        raise PersistedDataContractError(
            f"Walk-forward v3 {owner_label} tail count does not match its source"
        )
    for metric in _TAIL_METRICS:
        source_value = getattr(source, metric)
        evidence_value = getattr(owner, metric)
        if (source_value is None) != (evidence_value is None) or (
            source_value is not None
            and not _optional_float_equal(float(source_value), float(evidence_value))
        ):
            raise PersistedDataContractError(
                f"Walk-forward v3 {owner_label} {metric} does not match its source"
            )


def _validate_summary(
    summary: WalkForwardMetricSummaryModel,
    values: Sequence[float | None],
    *,
    window_count: int,
    owner_label: str,
) -> None:
    valid_values = [value for value in values if value is not None]
    if summary.window_count != window_count or summary.valid_count != len(valid_values):
        raise PersistedDataContractError(
            f"Walk-forward v3 {owner_label} evidence does not match source OOS rows"
        )
    expected_status = "sufficient" if len(valid_values) >= 3 else "insufficient_evidence"
    if summary.evidence_status != expected_status:
        raise PersistedDataContractError(
            f"Walk-forward v3 {owner_label} evidence does not match source OOS rows"
        )
    expected = (
        (None, None, None, None, None)
        if not valid_values
        else (
            mean(valid_values),
            median(valid_values),
            min(valid_values),
            max(valid_values),
            pstdev(valid_values),
        )
    )
    actual = (summary.mean, summary.median, summary.min, summary.max, summary.std)
    if any(
        not _optional_float_equal(left, right) for left, right in zip(actual, expected, strict=True)
    ):
        raise PersistedDataContractError(
            f"Walk-forward v3 {owner_label} evidence does not match source OOS rows"
        )


def _optional_float_equal(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)
