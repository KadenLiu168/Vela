from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from statistics import mean, median, pstdev
from typing import Any

from vela_core.walk_forward.window_splitter import WalkForwardWindow


@dataclass(frozen=True)
class WalkForwardWindowResult:
    window: WalkForwardWindow
    best_combo: dict[str, Any]
    oos_version: str
    train_sharpe: float | None
    oos_annualized_return: float | None
    oos_sharpe: float | None
    oos_max_drawdown: float | None
    baseline_annualized_return: float | None
    baseline_sharpe: float | None
    skipped: list[str]


@dataclass
class WalkForwardReport:
    windows: list[WalkForwardWindowResult] = field(default_factory=list)
    baseline_enabled: bool = False

    def aggregate(self) -> dict[str, dict[str, float | None]]:
        return {
            name: _summary([value for value in values if value is not None])
            for name, values in {
                "annualized_return": [item.oos_annualized_return for item in self.windows],
                "sharpe_ratio": [item.oos_sharpe for item in self.windows],
            }.items()
        }

    def baseline_differences(self) -> dict[str, float | int | None]:
        annualized_returns = [
            item.oos_annualized_return - item.baseline_annualized_return
            for item in self.windows
            if item.oos_annualized_return is not None
            and item.baseline_annualized_return is not None
        ]
        sharpes = [
            item.oos_sharpe - item.baseline_sharpe
            for item in self.windows
            if item.oos_sharpe is not None and item.baseline_sharpe is not None
        ]
        return {
            "annualized_return_mean": mean(annualized_returns) if annualized_returns else None,
            "annualized_return_count": len(annualized_returns),
            "sharpe_mean": mean(sharpes) if sharpes else None,
            "sharpe_count": len(sharpes),
        }


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
        if report.baseline_enabled:
            lines.append(
                "  Baseline annualized return difference: "
                f"{_difference(item.oos_annualized_return, item.baseline_annualized_return)}; "
                f"Sharpe difference: {_difference(item.oos_sharpe, item.baseline_sharpe)}"
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
    if report.baseline_enabled:
        differences = report.baseline_differences()
        lines += [
            "Baseline comparison",
            "  Annualized return difference mean: "
            f"{_metric(differences['annualized_return_mean'])} "
            f"({differences['annualized_return_count']} windows)",
            f"  Sharpe difference mean: {_metric(differences['sharpe_mean'])} "
            f"({differences['sharpe_count']} windows)",
        ]
    lines.append("Parameter stability")
    parameter_names = sorted({name for item in report.windows for name in item.best_combo})
    for name in parameter_names:
        values = ", ".join(
            f"window {index}={item.best_combo.get(name, 'n/a')}"
            for index, item in enumerate(report.windows, start=1)
        )
        lines.append(f"  {name}: {values}")
    return "\n".join(lines) + "\n"


def _difference(left: float | None, right: float | None) -> str:
    return "n/a" if left is None or right is None else f"{left - right:.6f}"


def _skip_summary(skipped: list[str]) -> str:
    reasons = Counter((item.partition(": ")[2] or item).splitlines()[0] for item in skipped)
    return "; ".join(f"{reason} ({count})" for reason, count in sorted(reasons.items()))
