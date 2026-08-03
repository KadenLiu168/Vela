from datetime import date

from vela_core.walk_forward.report import (
    WalkForwardBenchmarkResult,
    WalkForwardReport,
    WalkForwardWindowResult,
    format_report,
)
from vela_core.walk_forward.window_splitter import WalkForwardWindow


def test_format_report_includes_aggregate_stability_and_benchmark_comparisons() -> None:
    report = WalkForwardReport(
        windows=[
            WalkForwardWindowResult(
                window=WalkForwardWindow(
                    date(2020, 1, 1), date(2020, 12, 31), date(2021, 1, 1), date(2021, 12, 31)
                ),
                best_combo={"parameters.selection.top_n": 2},
                oos_version="wf-123456789abc",
                train_sharpe=1.0,
                oos_annualized_return=0.2,
                oos_sharpe=0.8,
                oos_max_drawdown=-0.1,
                benchmarks=(
                    _benchmark(
                        "equal_weight_monthly",
                        total_return=0.1,
                        annualized_return=0.15,
                        total_return_difference=0.2,
                        annualized_return_difference=0.05,
                    ),
                ),
                skipped=[],
            )
        ]
    )

    text = format_report(report)

    assert "2020-01-01 to 2020-12-31" in text
    assert "wf-123456789abc" in text
    assert "Parameter stability" in text
    assert "OOS maximum drawdown" in text
    assert "equal_weight_monthly comparison" in text
    assert "Strategy total return difference: 0.200000" in text
    assert "Strategy annualized return difference: 0.050000" in text
    assert "Maximum drawdown: -0.050000" in text
    assert "Volatility: 0.120000" in text
    assert "Sharpe ratio: 0.900000" in text


def test_format_report_keeps_null_benchmark_values_visible() -> None:
    report = WalkForwardReport(
        windows=[
            WalkForwardWindowResult(
                window=WalkForwardWindow(
                    date(2020, 1, 1), date(2020, 12, 31), date(2021, 1, 1), date(2021, 12, 31)
                ),
                best_combo={"parameters.selection.top_n": 2},
                oos_version="wf-123456789abc",
                train_sharpe=1.0,
                oos_annualized_return=None,
                oos_sharpe=None,
                oos_max_drawdown=-0.1,
                benchmarks=(
                    _benchmark(
                        "csi_300_buy_hold",
                        total_return=None,
                        annualized_return=None,
                        total_return_difference=None,
                        annualized_return_difference=None,
                    ),
                ),
                skipped=[],
            )
        ],
    )

    text = format_report(report)

    assert "Benchmark: csi_300_buy_hold (csi_300_buy_hold)" in text
    assert "Total return: n/a" in text
    assert "csi_300_buy_hold comparison" in text


def test_report_summarizes_skips_and_benchmark_differences() -> None:
    window = WalkForwardWindow(
        date(2020, 1, 1), date(2020, 12, 31), date(2021, 1, 1), date(2021, 12, 31)
    )
    report = WalkForwardReport(
        windows=[
            WalkForwardWindowResult(
                window,
                {"parameters.selection.top_n": 1},
                "wf-111111111111",
                1.0,
                0.2,
                0.8,
                -0.1,
                (
                    _benchmark(
                        "equal_weight_monthly",
                        total_return=0.1,
                        annualized_return=0.1,
                        total_return_difference=0.2,
                        annualized_return_difference=0.1,
                    ),
                ),
                ['{"x":1}: unscorable result'],
            ),
            WalkForwardWindowResult(
                window,
                {"parameters.selection.top_n": 2},
                "wf-222222222222",
                1.0,
                None,
                None,
                -0.2,
                (
                    _benchmark(
                        "equal_weight_monthly",
                        total_return=None,
                        annualized_return=None,
                        total_return_difference=None,
                        annualized_return_difference=None,
                    ),
                ),
                [],
            ),
        ],
    )

    assert report.benchmark_differences()["equal_weight_monthly"] == {
        "total_return_mean": 0.2,
        "total_return_count": 1,
        "annualized_return_mean": 0.1,
        "annualized_return_count": 1,
    }
    text = format_report(report)
    assert "Skip summary: unscorable result (1)" in text
    assert "equal_weight_monthly comparison" in text
    assert "parameters.selection.top_n: window 1=1, window 2=2" in text


def _benchmark(
    key: str,
    *,
    total_return: float | None,
    annualized_return: float | None,
    total_return_difference: float | None,
    annualized_return_difference: float | None,
) -> WalkForwardBenchmarkResult:
    return WalkForwardBenchmarkResult(
        key=key,
        name=key,
        total_return=total_return,
        annualized_return=annualized_return,
        max_drawdown=-0.05,
        volatility=0.12,
        sharpe_ratio=0.9,
        total_return_difference=total_return_difference,
        annualized_return_difference=annualized_return_difference,
    )
