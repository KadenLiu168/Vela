from __future__ import annotations

import json
import math
from collections.abc import Sequence
from decimal import Decimal
from statistics import mean, median, pstdev

from vela_core.models import BacktestBenchmark, BacktestRun
from vela_core.walk_forward.evidence import (
    BenchmarkKey,
    PersistedDataContractError,
    WalkForwardEvidenceV2,
    WalkForwardMetricSummaryModel,
)

_METRIC_VERSION = "benchmark_regime_metrics_v1"
_BENCHMARK_KEYS: tuple[BenchmarkKey, ...] = (
    "equal_weight_monthly",
    "csi_300_buy_hold",
)
_CAPM_METRICS = ("capm_alpha", "capm_beta", "capm_r_squared")
_CAPTURE_METRICS = ("up_capture_ratio", "down_capture_ratio")
_REGIME_METRICS = (*_CAPM_METRICS, *_CAPTURE_METRICS)


def validate_v2_regime_source_evidence(
    oos_rows: Sequence[BacktestRun], evidence: WalkForwardEvidenceV2
) -> None:
    sources: list[dict[str, BacktestBenchmark]] = []
    for oos in oos_rows:
        try:
            parameters = json.loads(oos.parameters_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise PersistedDataContractError(
                "Walk-forward v2 source OOS parameters are invalid"
            ) from exc
        if (
            not isinstance(parameters, dict)
            or parameters.get("benchmark_regime_metric_version") != _METRIC_VERSION
        ):
            raise PersistedDataContractError("Walk-forward v2 source OOS metric version is invalid")
        benchmarks = {benchmark.benchmark_key: benchmark for benchmark in oos.benchmarks}
        if set(benchmarks) != set(_BENCHMARK_KEYS) or len(oos.benchmarks) != 2:
            raise PersistedDataContractError(
                "Walk-forward v2 source OOS rows require exactly the two fixed benchmarks"
            )
        for key, benchmark in benchmarks.items():
            _validate_source_counts(key, benchmark)
        sources.append(benchmarks)

    for benchmark_key in _BENCHMARK_KEYS:
        benchmark_evidence = evidence.benchmarks[benchmark_key]
        for metric in _REGIME_METRICS:
            values = [getattr(source[benchmark_key], metric) for source in sources]
            _validate_summary(
                getattr(benchmark_evidence, metric),
                values,
                window_count=len(sources),
            )


def _validate_source_counts(benchmark_key: str, benchmark: BacktestBenchmark) -> None:
    if benchmark_key == "equal_weight_monthly" and any(
        getattr(benchmark, field) is not None
        for field in (*_CAPM_METRICS, "capm_observation_count")
    ):
        raise PersistedDataContractError(
            "Walk-forward v2 equal-weight source must not contain CAPM evidence"
        )

    if benchmark_key == "csi_300_buy_hold":
        _validate_observation_count(benchmark.capm_observation_count)
        if any(getattr(benchmark, field) is not None for field in _CAPM_METRICS) and (
            benchmark.capm_observation_count is None or benchmark.capm_observation_count < 2
        ):
            raise PersistedDataContractError(
                "Walk-forward v2 CAPM value has an invalid observation count"
            )

    for metric, count_field in (
        ("up_capture_ratio", "up_capture_observation_count"),
        ("down_capture_ratio", "down_capture_observation_count"),
    ):
        count = getattr(benchmark, count_field)
        _validate_observation_count(count)
        if getattr(benchmark, metric) is not None and count == 0:
            raise PersistedDataContractError(
                "Walk-forward v2 capture value has an invalid observation count"
            )


def _validate_observation_count(value: int | None) -> None:
    if type(value) is not int or value < 0:
        raise PersistedDataContractError(
            "Walk-forward v2 source observation count must be a non-negative integer"
        )


def _validate_summary(
    summary: WalkForwardMetricSummaryModel,
    values: Sequence[Decimal | None],
    *,
    window_count: int,
) -> None:
    valid_values = [float(value) for value in values if value is not None]
    if summary.window_count != window_count or summary.valid_count != len(valid_values):
        raise PersistedDataContractError("Walk-forward v2 evidence does not match source OOS rows")
    expected_status = "sufficient" if len(valid_values) >= 3 else "insufficient_evidence"
    if summary.evidence_status != expected_status:
        raise PersistedDataContractError("Walk-forward v2 evidence does not match source OOS rows")
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
        raise PersistedDataContractError("Walk-forward v2 evidence does not match source OOS rows")


def _optional_float_equal(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)
