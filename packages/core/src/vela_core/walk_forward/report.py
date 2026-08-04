from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from statistics import mean, median, pstdev
from typing import Any, Literal, TypedDict

from vela_core.walk_forward.window_splitter import WalkForwardWindow

EvidenceStatus = Literal["sufficient", "insufficient_evidence"]


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


@dataclass
class WalkForwardReport:
    windows: list[WalkForwardWindowResult] = field(default_factory=list)

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
