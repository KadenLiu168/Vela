from decimal import Decimal

from sqlalchemy.orm import Session

from vela_core.backtest_result_persistence import get_backtest_result
from vela_core.models import BacktestEquityCurve, BacktestRun


class BacktestReportNotFoundError(ValueError):
    pass


def export_backtest_report(session: Session, *, run_id: int) -> str:
    run = get_backtest_result(session, run_id=run_id)
    if run is None:
        raise BacktestReportNotFoundError(f"Backtest run not found: {run_id}")

    return _format_report(run)


def _format_report(run: BacktestRun) -> str:
    lines = [
        "Backtest Report",
        f"Run id: {run.id}",
        f"Strategy: {run.strategy_id}",
        f"Config version: {run.config_version}",
        f"Date range: {run.start_date.isoformat()} to {run.end_date.isoformat()}",
        f"Status: {run.status}",
        f"Started at: {run.started_at.isoformat()}",
        f"Finished at: {_format_optional(run.finished_at)}",
        f"Parameters: {run.parameters_json}",
    ]
    if run.error_message:
        lines.append(f"Error: {run.error_message}")

    run_recovery = _format_drawdown_recovery(
        run.longest_drawdown_recovery_date,
        run.longest_drawdown_duration_sessions,
        run.longest_drawdown_peak_date,
        run.longest_drawdown_trough_date,
    )
    lines.extend(
        [
            "Metrics:",
            f"- Total return: {_format_optional(run.total_return)}",
            f"- Annualized return: {_format_optional(run.annualized_return)}",
            f"- Max drawdown: {_format_optional(run.max_drawdown)}",
            f"- Volatility: {_format_optional(run.volatility)}",
            f"- Sharpe ratio: {_format_optional(run.sharpe_ratio)}",
            f"- Sortino (rf MAR, 252D): {_format_optional(run.sortino_ratio)}",
            f"- Calmar (calendar CAGR / |MaxDD|): {_format_optional(run.calmar_ratio)}",
            "- Longest drawdown duration (official sessions): "
            f"{_format_optional(run.longest_drawdown_duration_sessions)}",
            f"- Longest drawdown peak: {_format_optional(run.longest_drawdown_peak_date)}",
            f"- Longest drawdown trough: {_format_optional(run.longest_drawdown_trough_date)}",
            f"- Longest drawdown recovery: {run_recovery}",
            "Equity Curve Summary:",
            f"- Points: {len(run.equity_curve)}",
        ]
    )

    if not run.equity_curve:
        lines.append("- Rows: none")
    else:
        first = run.equity_curve[0]
        last = run.equity_curve[-1]
        min_net_value = min(
            run.equity_curve,
            key=lambda row: (row.net_value, row.trade_date, row.id),
        )
        max_net_value = max(
            run.equity_curve,
            key=lambda row: (row.net_value, row.trade_date, row.id),
        )
        lines.extend(
            [
                f"- First: {_format_curve_row(first)}",
                f"- Last: {_format_curve_row(last)}",
                f"- Min net value: {_format_curve_row(min_net_value)}",
                f"- Max net value: {_format_curve_row(max_net_value)}",
            ]
        )

    for benchmark in run.benchmarks:
        benchmark_recovery = _format_drawdown_recovery(
            benchmark.longest_drawdown_recovery_date,
            benchmark.longest_drawdown_duration_sessions,
            benchmark.longest_drawdown_peak_date,
            benchmark.longest_drawdown_trough_date,
        )
        lines.extend(
            [
                f"Benchmark: {benchmark.display_name}",
                f"- Total return: {_format_optional(benchmark.total_return)}",
                f"- Annualized return: {_format_optional(benchmark.annualized_return)}",
                f"- Max drawdown: {_format_optional(benchmark.max_drawdown)}",
                f"- Volatility: {_format_optional(benchmark.volatility)}",
                f"- Sharpe ratio: {_format_optional(benchmark.sharpe_ratio)}",
                f"- Sortino (rf MAR, 252D): {_format_optional(benchmark.sortino_ratio)}",
                f"- Calmar (calendar CAGR / |MaxDD|): {_format_optional(benchmark.calmar_ratio)}",
                "- Longest drawdown duration (official sessions): "
                f"{_format_optional(benchmark.longest_drawdown_duration_sessions)}",
                "- Longest drawdown peak: "
                f"{_format_optional(benchmark.longest_drawdown_peak_date)}",
                "- Longest drawdown trough: "
                f"{_format_optional(benchmark.longest_drawdown_trough_date)}",
                f"- Longest drawdown recovery: {benchmark_recovery}",
                f"- Tracking error (252D): {_format_optional(benchmark.tracking_error)}",
                f"- Information ratio (252D): {_format_optional(benchmark.information_ratio)}",
                "- Strategy total return difference: "
                f"{_difference(run.total_return, benchmark.total_return)}",
                "- Strategy annualized return difference: "
                f"{_difference(run.annualized_return, benchmark.annualized_return)}",
            ]
        )

    return "\n".join(lines) + "\n"


def _format_curve_row(row: BacktestEquityCurve) -> str:
    return (
        f"{row.trade_date.isoformat()} net_value={row.net_value} cash={row.cash} "
        f"market_value={row.market_value} total_assets={row.total_assets}"
    )


def _format_optional(value: object | None) -> str:
    return "n/a" if value is None else str(value)


def _format_drawdown_recovery(
    value: object | None,
    duration: int | None,
    peak_date: object | None,
    trough_date: object | None,
) -> str:
    if value is not None:
        return str(value)
    if duration is not None and duration > 0 and peak_date is not None and trough_date is not None:
        return "ongoing"
    return "n/a"


def _difference(left: Decimal | None, right: Decimal | None) -> str:
    return "n/a" if left is None or right is None else str(left - right)
