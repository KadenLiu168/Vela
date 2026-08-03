from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from statistics import mean, median, pstdev
from typing import Any

from vela_core.walk_forward.window_splitter import WalkForwardWindow


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


@dataclass(frozen=True)
class WalkForwardWindowResult:
    window: WalkForwardWindow
    best_combo: dict[str, Any]
    oos_version: str
    train_sharpe: float | None
    oos_annualized_return: float | None
    oos_sharpe: float | None
    oos_max_drawdown: float | None
    benchmarks: tuple[WalkForwardBenchmarkResult, ...]
    skipped: list[str]


@dataclass
class WalkForwardReport:
    windows: list[WalkForwardWindowResult] = field(default_factory=list)

    def aggregate(self) -> dict[str, dict[str, float | None]]:
        return {
            name: _summary([value for value in values if value is not None])
            for name, values in {
                "annualized_return": [item.oos_annualized_return for item in self.windows],
                "sharpe_ratio": [item.oos_sharpe for item in self.windows],
            }.items()
        }

    def benchmark_differences(self) -> dict[str, dict[str, float | int | None]]:
        result: dict[str, dict[str, float | int | None]] = {}
        for key in sorted(
            {benchmark.key for item in self.windows for benchmark in item.benchmarks}
        ):
            total_differences = [
                benchmark.total_return_difference
                for item in self.windows
                for benchmark in item.benchmarks
                if benchmark.key == key and benchmark.total_return_difference is not None
            ]
            annualized_differences = [
                benchmark.annualized_return_difference
                for item in self.windows
                for benchmark in item.benchmarks
                if benchmark.key == key and benchmark.annualized_return_difference is not None
            ]
            result[key] = {
                "total_return_mean": mean(total_differences) if total_differences else None,
                "total_return_count": len(total_differences),
                "annualized_return_mean": (
                    mean(annualized_differences) if annualized_differences else None
                ),
                "annualized_return_count": len(annualized_differences),
            }
        return result


def _summary(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "median": None, "min": None, "max": None, "std": None}
    return {
        "mean": mean(values),
        "median": median(values),
        "min": min(values),
        "max": max(values),
        "std": pstdev(values),
    }


def _metric(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.6f}"


def format_report(report: WalkForwardReport) -> str:
    lines = ["Walk-forward report", ""]
    for index, item in enumerate(report.windows, start=1):
        lines += [
            f"Window {index}: train {item.window.train_start} to {item.window.train_end}; "
            f"OOS {item.window.test_start} to {item.window.test_end}",
            f"  Best parameters: {item.best_combo}",
            f"  OOS version: {item.oos_version}",
            f"  Train Sharpe: {_metric(item.train_sharpe)}; "
            f"OOS annualized return: {_metric(item.oos_annualized_return)}; "
            f"OOS Sharpe: {_metric(item.oos_sharpe)}; "
            f"OOS maximum drawdown: {_metric(item.oos_max_drawdown)}",
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
        lines.append(
            f"  {name}: mean={_metric(stats['mean'])}, median={_metric(stats['median'])}, "
            f"min={_metric(stats['min'])}, max={_metric(stats['max'])}, "
            f"std={_metric(stats['std'])}"
        )
    for key, differences in report.benchmark_differences().items():
        lines.append(
            f"{key} comparison: total return difference mean="
            f"{_metric(differences['total_return_mean'])} "
            f"({differences['total_return_count']} windows); "
            f"annualized return difference mean="
            f"{_metric(differences['annualized_return_mean'])} "
            f"({differences['annualized_return_count']} windows)"
        )
    lines.append("Parameter stability")
    parameter_names = sorted({name for item in report.windows for name in item.best_combo})
    for name in parameter_names:
        values = ", ".join(
            f"window {index}={item.best_combo.get(name, 'n/a')}"
            for index, item in enumerate(report.windows, start=1)
        )
        lines.append(f"  {name}: {values}")
    return "\n".join(lines) + "\n"


def _skip_summary(skipped: list[str]) -> str:
    reasons = Counter((item.partition(": ")[2] or item).splitlines()[0] for item in skipped)
    return "; ".join(f"{reason} ({count})" for reason, count in sorted(reasons.items()))
