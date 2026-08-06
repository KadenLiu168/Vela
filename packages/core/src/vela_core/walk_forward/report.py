from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from statistics import mean, median, pstdev
from typing import Any, Literal, TypedDict

from vela_core.walk_forward.evidence import (
    WalkForwardEvidenceV3,
    WalkForwardTailDistributionOwnerModel,
)
from vela_core.walk_forward.window_splitter import WalkForwardWindow

EvidenceStatus = Literal["sufficient", "insufficient_evidence"]
MINIMUM_PUBLICATION_OBSERVATIONS = 100
TAIL_OWNER_KEYS = ("strategy", "equal_weight_monthly", "csi_300_buy_hold")
TAIL_METRICS = (
    "historical_var_95",
    "historical_cvar_95",
    "return_skewness",
    "return_excess_kurtosis",
)


class WalkForwardMetricSummary(TypedDict):
    mean: float | None
    median: float | None
    min: float | None
    max: float | None
    std: float | None
    window_count: int
    valid_count: int
    evidence_status: EvidenceStatus


class WalkForwardRateSummary(TypedDict):
    numerator: int
    denominator: int
    value: float | None
    window_count: int
    valid_count: int
    evidence_status: EvidenceStatus


class WalkForwardBenchmarkComparison(TypedDict):
    total_return: WalkForwardMetricSummary
    annualized_return: WalkForwardMetricSummary
    tracking_error: WalkForwardMetricSummary
    information_ratio: WalkForwardMetricSummary
    outperformance_rate: WalkForwardRateSummary


class WalkForwardParameterStability(TypedDict):
    value_frequencies: dict[str, int]
    transition_count: int
    comparison_count: int
    transition_rate: float | None


@dataclass(frozen=True)
class WalkForwardBenchmarkResult:
    key: str
    name: str
    total_return: float | None
    annualized_return: float | None
    max_drawdown: float | None
    volatility: float | None
    sharpe_ratio: float | None
    total_return_difference: float | None
    annualized_return_difference: float | None
    tracking_error: float | None = None
    information_ratio: float | None = None
    capm_alpha: float | None = None
    capm_beta: float | None = None
    capm_r_squared: float | None = None
    capm_observation_count: int | None = None
    up_capture_ratio: float | None = None
    up_capture_observation_count: int | None = None
    down_capture_ratio: float | None = None
    down_capture_observation_count: int | None = None
    historical_var_95: float | None = None
    historical_cvar_95: float | None = None
    return_skewness: float | None = None
    return_excess_kurtosis: float | None = None
    distribution_observation_count: int | None = None
    tail_observation_count: int | None = None


@dataclass(frozen=True)
class WalkForwardWindowResult:
    window: WalkForwardWindow
    best_combo: dict[str, Any]
    oos_version: str
    train_sharpe: float | None
    oos_total_return: float | None
    oos_annualized_return: float | None
    oos_sharpe: float | None
    oos_max_drawdown: float | None
    oos_volatility: float | None
    benchmarks: tuple[WalkForwardBenchmarkResult, ...]
    skipped: list[str]
    oos_sortino: float | None = None
    oos_calmar: float | None = None
    oos_longest_drawdown_duration_sessions: int | None = None
    oos_backtest_id: int | None = None
    candidate_count: int = 0
    eligible_count: int = 0
    skipped_count: int = 0
    skip_reason_counts: dict[str, int] = field(default_factory=dict)
    historical_var_95: float | None = None
    historical_cvar_95: float | None = None
    return_skewness: float | None = None
    return_excess_kurtosis: float | None = None
    distribution_observation_count: int | None = None
    tail_observation_count: int | None = None


@dataclass
class WalkForwardReport:
    windows: list[WalkForwardWindowResult] = field(default_factory=list)
    walk_forward_run_id: int | None = None

    def evidence_document(self) -> WalkForwardEvidenceV3:
        benchmark_comparisons = self.benchmark_differences()
        benchmark_regime = self.benchmark_regime_evidence()
        return WalkForwardEvidenceV3.model_validate(
            {
                "metrics": self.aggregate(),
                "positive_window_rate": self.positive_window_rate(),
                "generalization_gap": self.generalization_gap(),
                "benchmarks": {
                    key: {
                        "total_return_difference": value["total_return"],
                        "annualized_return_difference": value["annualized_return"],
                        "tracking_error": value["tracking_error"],
                        "information_ratio": value["information_ratio"],
                        "outperformance_rate": value["outperformance_rate"],
                        **benchmark_regime[key],
                    }
                    for key, value in benchmark_comparisons.items()
                },
                "parameter_stability": self.parameter_stability(),
                "tail_distribution": self.tail_distribution_evidence(),
            }
        )

    def tail_distribution_evidence(self) -> dict[str, object]:
        """Per-window and aggregate one-day historical distribution evidence.

        Aggregates are descriptive statistics across independent per-window
        metric estimates; they are not calculated from a combined or stitched
        return distribution. Nulls do not contribute; valid zeros do.
        """
        per_window: list[dict[str, object]] = []
        for index, item in enumerate(self.windows):
            owners: dict[str, object] = {
                "strategy": _tail_owner(
                    historical_var_95=item.historical_var_95,
                    historical_cvar_95=item.historical_cvar_95,
                    return_skewness=item.return_skewness,
                    return_excess_kurtosis=item.return_excess_kurtosis,
                    observation_count=item.distribution_observation_count,
                    tail_observation_count=item.tail_observation_count,
                )
            }
            for benchmark in item.benchmarks:
                owners[benchmark.key] = _tail_owner(
                    historical_var_95=benchmark.historical_var_95,
                    historical_cvar_95=benchmark.historical_cvar_95,
                    return_skewness=benchmark.return_skewness,
                    return_excess_kurtosis=benchmark.return_excess_kurtosis,
                    observation_count=benchmark.distribution_observation_count,
                    tail_observation_count=benchmark.tail_observation_count,
                )
            per_window.append({"ordinal": index, "owners": owners})

        aggregates: dict[str, dict[str, object]] = {}
        for owner in TAIL_OWNER_KEYS:
            aggregates[owner] = {
                metric: _summary(
                    self._tail_values(owner, metric),
                    window_count=len(self.windows),
                )
                for metric in TAIL_METRICS
            }
        return {"per_window": per_window, "aggregates": aggregates}

    def _tail_values(self, owner: str, metric: str) -> list[float | None]:
        if owner == "strategy":
            return [getattr(item, metric) for item in self.windows]
        return [
            getattr(benchmark, metric)
            for item in self.windows
            for benchmark in item.benchmarks
            if benchmark.key == owner
        ]

    def aggregate(self) -> dict[str, WalkForwardMetricSummary]:
        values_by_metric: dict[str, Sequence[float | int | None]] = {
            "total_return": [item.oos_total_return for item in self.windows],
            "annualized_return": [item.oos_annualized_return for item in self.windows],
            "sharpe_ratio": [item.oos_sharpe for item in self.windows],
            "max_drawdown": [item.oos_max_drawdown for item in self.windows],
            "volatility": [item.oos_volatility for item in self.windows],
            "sortino_ratio": [item.oos_sortino for item in self.windows],
            "calmar_ratio": [item.oos_calmar for item in self.windows],
            "longest_drawdown_duration_sessions": [
                item.oos_longest_drawdown_duration_sessions for item in self.windows
            ],
        }
        return {
            name: _summary(values, window_count=len(self.windows))
            for name, values in values_by_metric.items()
        }

    def positive_window_rate(self) -> WalkForwardRateSummary:
        values = [item.oos_total_return for item in self.windows]
        return _rate(values, window_count=len(self.windows))

    def generalization_gap(self) -> WalkForwardMetricSummary:
        gaps = [
            item.train_sharpe - item.oos_sharpe
            for item in self.windows
            if item.train_sharpe is not None and item.oos_sharpe is not None
        ]
        return _summary(gaps, window_count=len(self.windows))

    def benchmark_differences(self) -> dict[str, WalkForwardBenchmarkComparison]:
        result: dict[str, WalkForwardBenchmarkComparison] = {}
        for key in sorted(
            {benchmark.key for item in self.windows for benchmark in item.benchmarks}
        ):
            total_differences = [
                benchmark.total_return_difference
                for item in self.windows
                for benchmark in item.benchmarks
                if benchmark.key == key
            ]
            annualized_differences = [
                benchmark.annualized_return_difference
                for item in self.windows
                for benchmark in item.benchmarks
                if benchmark.key == key
            ]
            tracking_errors = [
                benchmark.tracking_error
                for item in self.windows
                for benchmark in item.benchmarks
                if benchmark.key == key
            ]
            information_ratios = [
                benchmark.information_ratio
                for item in self.windows
                for benchmark in item.benchmarks
                if benchmark.key == key
            ]
            result[key] = {
                "total_return": _summary(
                    total_differences,
                    window_count=len(self.windows),
                ),
                "annualized_return": _summary(
                    annualized_differences,
                    window_count=len(self.windows),
                ),
                "tracking_error": _summary(
                    tracking_errors,
                    window_count=len(self.windows),
                ),
                "information_ratio": _summary(
                    information_ratios,
                    window_count=len(self.windows),
                ),
                "outperformance_rate": _rate(
                    total_differences,
                    window_count=len(self.windows),
                ),
            }
        return result

    def benchmark_regime_evidence(self) -> dict[str, dict[str, WalkForwardMetricSummary]]:
        regime_metrics = (
            "capm_alpha",
            "capm_beta",
            "capm_r_squared",
            "up_capture_ratio",
            "down_capture_ratio",
        )
        result: dict[str, dict[str, WalkForwardMetricSummary]] = {}
        for key in sorted(
            {benchmark.key for item in self.windows for benchmark in item.benchmarks}
        ):
            values_by_metric = {
                metric: [
                    getattr(benchmark, metric)
                    for item in self.windows
                    for benchmark in item.benchmarks
                    if benchmark.key == key
                ]
                for metric in regime_metrics
            }
            result[key] = {
                metric: _summary(values, window_count=len(self.windows))
                for metric, values in values_by_metric.items()
            }
        return result

    def parameter_stability(self) -> dict[str, WalkForwardParameterStability]:
        result: dict[str, WalkForwardParameterStability] = {}
        parameter_names = sorted({name for item in self.windows for name in item.best_combo})
        for name in parameter_names:
            canonical_values = [
                _canonical_value(item.best_combo[name])
                for item in self.windows
                if name in item.best_combo
            ]
            transition_count = 0
            comparison_count = 0
            previous: str | None = None
            for item in self.windows:
                if name not in item.best_combo:
                    previous = None
                    continue
                current = _canonical_value(item.best_combo[name])
                if previous is not None:
                    comparison_count += 1
                    if current != previous:
                        transition_count += 1
                previous = current
            result[name] = {
                "value_frequencies": dict(Counter(canonical_values)),
                "transition_count": transition_count,
                "comparison_count": comparison_count,
                "transition_rate": (
                    transition_count / comparison_count if comparison_count else None
                ),
            }
        return result


def _tail_owner(
    *,
    historical_var_95: float | None,
    historical_cvar_95: float | None,
    return_skewness: float | None,
    return_excess_kurtosis: float | None,
    observation_count: int | None,
    tail_observation_count: int | None,
) -> dict[str, object]:
    effective_count = 0 if observation_count is None else observation_count
    tail_count = 0 if tail_observation_count is None else tail_observation_count
    status: EvidenceStatus = (
        "sufficient"
        if effective_count >= MINIMUM_PUBLICATION_OBSERVATIONS
        else "insufficient_evidence"
    )
    return WalkForwardTailDistributionOwnerModel.model_validate(
        {
            "historical_var_95": historical_var_95,
            "historical_cvar_95": historical_cvar_95,
            "return_skewness": return_skewness,
            "return_excess_kurtosis": return_excess_kurtosis,
            "observation_count": effective_count,
            "tail_observation_count": tail_count,
            "evidence_status": status,
        }
    ).model_dump(mode="json")


def _summary(
    values: Sequence[float | int | None],
    *,
    window_count: int,
) -> WalkForwardMetricSummary:
    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return {
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "std": None,
            "window_count": window_count,
            "valid_count": 0,
            "evidence_status": "insufficient_evidence",
        }
    return {
        "mean": mean(valid_values),
        "median": median(valid_values),
        "min": min(valid_values),
        "max": max(valid_values),
        "std": pstdev(valid_values),
        "window_count": window_count,
        "valid_count": len(valid_values),
        "evidence_status": _evidence_status(len(valid_values)),
    }


def _rate(
    values: Sequence[float | None],
    *,
    window_count: int,
) -> WalkForwardRateSummary:
    valid_values = [value for value in values if value is not None]
    numerator = sum(value > 0 for value in valid_values)
    denominator = len(valid_values)
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
        "window_count": window_count,
        "valid_count": denominator,
        "evidence_status": _evidence_status(denominator),
    }


def _evidence_status(valid_count: int) -> EvidenceStatus:
    return "sufficient" if valid_count >= 3 else "insufficient_evidence"


def _canonical_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _metric(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.6f}"


def _format_summary(
    stats: WalkForwardMetricSummary,
    *,
    minimum_label: str = "min",
) -> str:
    return (
        f"mean={_metric(stats['mean'])}, median={_metric(stats['median'])}, "
        f"{minimum_label}={_metric(stats['min'])}, max={_metric(stats['max'])}, "
        f"std={_metric(stats['std'])}, "
        f"valid={stats['valid_count']}/{stats['window_count']}, "
        f"evidence={stats['evidence_status']}"
    )


def _format_rate(rate: WalkForwardRateSummary) -> str:
    return (
        f"{rate['numerator']}/{rate['denominator']}="
        f"{_metric(rate['value'])}, valid={rate['valid_count']}/{rate['window_count']}, "
        f"evidence={rate['evidence_status']}"
    )


def format_report(report: WalkForwardReport) -> str:
    lines = ["Walk-forward report", ""]
    for index, item in enumerate(report.windows, start=1):
        lines += [
            f"Window {index}: train {item.window.train_start} to {item.window.train_end}; "
            f"OOS {item.window.test_start} to {item.window.test_end}",
            f"  Best parameters: {item.best_combo}",
            f"  OOS version: {item.oos_version}",
            f"  Train Sharpe: {_metric(item.train_sharpe)}; "
            f"OOS total return: {_metric(item.oos_total_return)}; "
            f"OOS annualized return: {_metric(item.oos_annualized_return)}; "
            f"OOS Sharpe: {_metric(item.oos_sharpe)}; "
            f"OOS maximum drawdown: {_metric(item.oos_max_drawdown)}; "
            f"OOS volatility: {_metric(item.oos_volatility)}; "
            f"OOS Sortino: {_metric(item.oos_sortino)}; "
            f"OOS Calmar: {_metric(item.oos_calmar)}; "
            "OOS longest drawdown duration: "
            f"{_metric(item.oos_longest_drawdown_duration_sessions)}",
            f"  Skipped combinations: {len(item.skipped)}",
            "  Distribution (1D historical loss; positive losses): "
            f"VaR95={_metric(item.historical_var_95)}, "
            f"CVaR95={_metric(item.historical_cvar_95)}, "
            f"skewness={_metric(item.return_skewness)}, "
            f"excess_kurtosis={_metric(item.return_excess_kurtosis)}, "
            f"observations={_metric(item.distribution_observation_count)}, "
            f"tail={_metric(item.tail_observation_count)}",
        ]
        for benchmark in item.benchmarks:
            lines.extend(
                [
                    f"  Benchmark: {benchmark.name} ({benchmark.key})",
                    f"    Total return: {_metric(benchmark.total_return)}",
                    f"    Annualized return: {_metric(benchmark.annualized_return)}",
                    f"    Maximum drawdown: {_metric(benchmark.max_drawdown)}",
                    f"    Volatility: {_metric(benchmark.volatility)}",
                    f"    Sharpe ratio: {_metric(benchmark.sharpe_ratio)}",
                    f"    Tracking error (252D): {_metric(benchmark.tracking_error)}",
                    f"    Information ratio (252D): {_metric(benchmark.information_ratio)}",
                    "    Strategy total return difference: "
                    f"{_metric(benchmark.total_return_difference)}",
                    "    Strategy annualized return difference: "
                    f"{_metric(benchmark.annualized_return_difference)}",
                ]
            )
            if benchmark.key == "csi_300_buy_hold":
                lines.extend(
                    [
                        "    CSI 300 ETF proxy Alpha (252D compounded): "
                        f"{_metric(benchmark.capm_alpha)}",
                        f"    CSI 300 ETF proxy Beta: {_metric(benchmark.capm_beta)}",
                        f"    CSI 300 ETF proxy R-squared: {_metric(benchmark.capm_r_squared)}",
                        "    CAPM observation count (daily sessions): "
                        f"{_metric(benchmark.capm_observation_count)}",
                    ]
                )
            lines.extend(
                [
                    "    Monthly Up Capture ratio (benchmark up months): "
                    f"{_metric(benchmark.up_capture_ratio)}",
                    "    Up capture selected months: "
                    f"{_metric(benchmark.up_capture_observation_count)}",
                    "    Monthly Down Capture ratio (benchmark down months): "
                    f"{_metric(benchmark.down_capture_ratio)}",
                    "    Down capture selected months: "
                    f"{_metric(benchmark.down_capture_observation_count)}",
                    "    Distribution (1D historical loss; positive losses): "
                    f"VaR95={_metric(benchmark.historical_var_95)}, "
                    f"CVaR95={_metric(benchmark.historical_cvar_95)}, "
                    f"skewness={_metric(benchmark.return_skewness)}, "
                    f"excess_kurtosis={_metric(benchmark.return_excess_kurtosis)}, "
                    f"observations={_metric(benchmark.distribution_observation_count)}, "
                    f"tail={_metric(benchmark.tail_observation_count)}",
                ]
            )
        if item.skipped:
            lines.append(f"  Skip summary: {_skip_summary(item.skipped)}")

    lines += ["", "OOS aggregate statistics"]
    for name, stats in report.aggregate().items():
        minimum_label = "worst" if name == "max_drawdown" else "min"
        lines.append(f"  {name}: {_format_summary(stats, minimum_label=minimum_label)}")

    lines.append(f"OOS positive-window rate: {_format_rate(report.positive_window_rate())}")
    lines.append(
        f"IS/OOS Sharpe generalization gap: {_format_summary(report.generalization_gap())}"
    )
    for key, comparison in report.benchmark_differences().items():
        lines.append(f"{key} comparison:")
        lines.append(
            "  total return difference: "
            f"{_format_summary(comparison['total_return'], minimum_label='worst')}"
        )
        lines.append(
            "  annualized return difference: "
            f"{_format_summary(comparison['annualized_return'], minimum_label='worst')}"
        )
        lines.append(f"  tracking error (252D): {_format_summary(comparison['tracking_error'])}")
        lines.append(
            f"  information ratio (252D): {_format_summary(comparison['information_ratio'])}"
        )
        lines.append(f"  outperformance rate: {_format_rate(comparison['outperformance_rate'])}")
    for key, regime in report.benchmark_regime_evidence().items():
        lines.append(f"{key} benchmark-regime evidence:")
        for metric, stats in regime.items():
            lines.append(f"  {metric}: {_format_summary(stats)}")

    lines.append(
        "Tail-distribution aggregates (descriptive statistics across independent "
        "window estimates, not a combined-distribution risk value)"
    )
    tail = report.tail_distribution_evidence()
    for owner in TAIL_OWNER_KEYS:
        lines.append(f"{owner}:")
        for metric in TAIL_METRICS:
            assert isinstance(tail["aggregates"], dict)
            owner_stats = tail["aggregates"][owner]
            assert isinstance(owner_stats, dict)
            stats = owner_stats[metric]
            assert isinstance(stats, dict)
            lines.append(f"  {metric}: {_format_summary(stats)}")

    lines.append("Parameter stability")
    stability = report.parameter_stability()
    parameter_names = sorted(stability)
    for name in parameter_names:
        values = ", ".join(
            f"window {index}={item.best_combo.get(name, 'n/a')}"
            for index, item in enumerate(report.windows, start=1)
        )
        stability_stats = stability[name]
        lines.append(
            f"  {name}: {values}; frequencies={stability_stats['value_frequencies']}; "
            f"transitions={stability_stats['transition_count']}/"
            f"{stability_stats['comparison_count']}; "
            f"transition_rate={_metric(stability_stats['transition_rate'])}"
        )
    return "\n".join(lines) + "\n"


def _skip_summary(skipped: list[str]) -> str:
    reasons = Counter((item.partition(": ")[2] or item).splitlines()[0] for item in skipped)
    return "; ".join(f"{reason} ({count})" for reason, count in sorted(reasons.items()))
