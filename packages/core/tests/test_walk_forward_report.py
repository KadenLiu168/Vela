from datetime import date

import pytest
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
                oos_total_return=0.3,
                oos_annualized_return=0.2,
                oos_sharpe=0.8,
                oos_max_drawdown=-0.1,
                oos_volatility=0.18,
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
                oos_total_return=None,
                oos_annualized_return=None,
                oos_sharpe=None,
                oos_max_drawdown=-0.1,
                oos_volatility=None,
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
                0.3,
                0.2,
                0.8,
                -0.1,
                0.18,
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
                None,
                -0.2,
                None,
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

    comparison = report.benchmark_differences()["equal_weight_monthly"]
    assert comparison["total_return"] == {
        "mean": 0.2,
        "median": 0.2,
        "min": 0.2,
        "max": 0.2,
        "std": 0.0,
        "window_count": 2,
        "valid_count": 1,
        "evidence_status": "insufficient_evidence",
    }
    assert comparison["annualized_return"]["mean"] == 0.1
    text = format_report(report)
    assert "Skip summary: unscorable result (1)" in text
    assert "equal_weight_monthly comparison" in text
    assert "parameters.selection.top_n: window 1=1, window 2=2" in text


def test_report_aggregates_five_metrics_with_local_evidence() -> None:
    report = WalkForwardReport(
        windows=[
            _result(
                1,
                best_combo={"parameters.selection.top_n": 1},
                oos_total_return=0.2,
                oos_annualized_return=0.1,
                oos_sharpe=0.8,
                oos_max_drawdown=-0.1,
                oos_volatility=0.2,
            ),
            _result(
                2,
                best_combo={"parameters.selection.top_n": 1},
                oos_total_return=0.0,
                oos_annualized_return=None,
                oos_sharpe=None,
                oos_max_drawdown=-0.3,
                oos_volatility=None,
            ),
            _result(
                3,
                best_combo={"parameters.selection.top_n": 2},
                oos_total_return=None,
                oos_annualized_return=0.3,
                oos_sharpe=0.4,
                oos_max_drawdown=None,
                oos_volatility=0.4,
            ),
        ]
    )

    aggregate = report.aggregate()

    assert aggregate["total_return"] == {
        "mean": 0.1,
        "median": 0.1,
        "min": 0.0,
        "max": 0.2,
        "std": 0.1,
        "window_count": 3,
        "valid_count": 2,
        "evidence_status": "insufficient_evidence",
    }
    assert aggregate["annualized_return"]["valid_count"] == 2
    assert aggregate["sharpe_ratio"]["valid_count"] == 2
    assert aggregate["max_drawdown"]["min"] == -0.3
    assert aggregate["volatility"]["valid_count"] == 2
    assert "worst=-0.300000" in format_report(report)


def test_report_aggregates_expanded_metrics_with_metric_local_evidence() -> None:
    report = WalkForwardReport(
        windows=[
            _result(
                1,
                best_combo={"parameters.selection.top_n": 1},
                oos_sortino=1.0,
                oos_calmar=2.0,
                oos_longest_drawdown_duration_sessions=3,
                benchmark_active_metrics={
                    "equal_weight_monthly": (0.03, 1.1),
                    "csi_300_buy_hold": (None, None),
                },
            ),
            _result(
                2,
                best_combo={"parameters.selection.top_n": 1},
                oos_sortino=0.5,
                oos_calmar=None,
                oos_longest_drawdown_duration_sessions=0,
                benchmark_active_metrics={
                    "equal_weight_monthly": (0.04, 1.2),
                    "csi_300_buy_hold": (0.05, 0.8),
                },
            ),
            _result(
                3,
                best_combo={"parameters.selection.top_n": 2},
                oos_sortino=0.2,
                oos_calmar=1.0,
                oos_longest_drawdown_duration_sessions=None,
                benchmark_active_metrics={
                    "equal_weight_monthly": (0.05, 1.3),
                    "csi_300_buy_hold": (0.06, 0.9),
                },
            ),
        ]
    )

    aggregate = report.aggregate()

    assert aggregate["sortino_ratio"]["valid_count"] == 3
    assert aggregate["calmar_ratio"]["valid_count"] == 2
    assert aggregate["longest_drawdown_duration_sessions"]["valid_count"] == 2
    comparisons = report.benchmark_differences()
    assert comparisons["equal_weight_monthly"]["tracking_error"]["valid_count"] == 3
    assert comparisons["equal_weight_monthly"]["information_ratio"]["mean"] == pytest.approx(1.2)
    assert comparisons["csi_300_buy_hold"]["tracking_error"]["valid_count"] == 2
    assert comparisons["csi_300_buy_hold"]["information_ratio"]["valid_count"] == 2
    text = format_report(report)
    assert "OOS Sortino" in text
    assert "OOS longest drawdown duration" in text
    assert "Tracking error" in text
    assert "Information ratio" in text


def test_report_keeps_zero_valid_observations_explicit_and_undefined_rates_null() -> None:
    report = WalkForwardReport(
        windows=[
            _result(
                1,
                best_combo={"parameters.selection.top_n": 1},
                train_sharpe=None,
                oos_total_return=None,
                oos_annualized_return=None,
                oos_sharpe=None,
                oos_max_drawdown=None,
                oos_volatility=None,
                benchmark_differences={"equal_weight_monthly": (None, None)},
            )
        ]
    )

    assert report.aggregate()["total_return"] == {
        "mean": None,
        "median": None,
        "min": None,
        "max": None,
        "std": None,
        "window_count": 1,
        "valid_count": 0,
        "evidence_status": "insufficient_evidence",
    }
    assert report.positive_window_rate() == {
        "numerator": 0,
        "denominator": 0,
        "value": None,
        "window_count": 1,
        "valid_count": 0,
        "evidence_status": "insufficient_evidence",
    }
    comparison = report.benchmark_differences()["equal_weight_monthly"]
    assert comparison["total_return"]["valid_count"] == 0
    assert comparison["total_return"]["window_count"] == 1
    assert comparison["outperformance_rate"]["value"] is None


def test_report_calculates_positive_and_benchmark_win_rates_with_ties() -> None:
    report = WalkForwardReport(
        windows=[
            _result(
                1,
                best_combo={"parameters.selection.top_n": 1},
                oos_total_return=0.2,
                benchmark_differences={
                    "equal_weight_monthly": (0.1, 0.05),
                    "csi_300_buy_hold": (0.0, 0.0),
                },
            ),
            _result(
                2,
                best_combo={"parameters.selection.top_n": 1},
                oos_total_return=0.0,
                benchmark_differences={
                    "equal_weight_monthly": (0.0, 0.0),
                    "csi_300_buy_hold": (0.2, 0.1),
                },
            ),
            _result(
                3,
                best_combo={"parameters.selection.top_n": 2},
                oos_total_return=-0.1,
                benchmark_differences={
                    "equal_weight_monthly": (-0.2, -0.1),
                    "csi_300_buy_hold": (None, None),
                },
            ),
        ]
    )

    assert report.positive_window_rate() == {
        "numerator": 1,
        "denominator": 3,
        "value": 1 / 3,
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }
    comparisons = report.benchmark_differences()
    assert comparisons["equal_weight_monthly"]["total_return"] == {
        "mean": -1 / 30,
        "median": 0.0,
        "min": -0.2,
        "max": 0.1,
        "std": pytest.approx(0.12472191289246472),
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }
    assert comparisons["equal_weight_monthly"]["outperformance_rate"] == {
        "numerator": 1,
        "denominator": 3,
        "value": 1 / 3,
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }
    assert comparisons["csi_300_buy_hold"]["outperformance_rate"] == {
        "numerator": 1,
        "denominator": 2,
        "value": 0.5,
        "window_count": 3,
        "valid_count": 2,
        "evidence_status": "insufficient_evidence",
    }


def test_report_summarizes_generalization_gaps_and_parameter_transitions() -> None:
    report = WalkForwardReport(
        windows=[
            _result(
                1,
                best_combo={"parameters.momentum.short_window_days": 60},
                train_sharpe=1.2,
                oos_sharpe=0.5,
            ),
            _result(
                2,
                best_combo={"parameters.momentum.short_window_days": 60},
                train_sharpe=1.0,
                oos_sharpe=None,
            ),
            _result(
                3,
                best_combo={"parameters.momentum.short_window_days": 120},
                train_sharpe=None,
                oos_sharpe=0.7,
            ),
        ]
    )

    assert report.generalization_gap() == {
        "mean": 0.7,
        "median": 0.7,
        "min": 0.7,
        "max": 0.7,
        "std": 0.0,
        "window_count": 3,
        "valid_count": 1,
        "evidence_status": "insufficient_evidence",
    }
    assert report.parameter_stability() == {
        "parameters.momentum.short_window_days": {
            "value_frequencies": {"60": 2, "120": 1},
            "transition_count": 1,
            "comparison_count": 2,
            "transition_rate": 0.5,
        }
    }


def test_format_report_renders_evidence_contract_without_decision_or_curve_claims() -> None:
    report = WalkForwardReport(
        windows=[
            _result(
                index,
                best_combo={"parameters.selection.top_n": value},
                train_sharpe=1.0,
                oos_total_return=0.2,
                oos_annualized_return=0.1,
                oos_sharpe=0.8,
                oos_max_drawdown=-0.1,
                oos_volatility=0.2,
                benchmark_differences={
                    "equal_weight_monthly": (0.05, 0.02),
                    "csi_300_buy_hold": (-0.01, -0.02),
                },
            )
            for index, value in enumerate((1, 1, 2), start=1)
        ]
    )

    text = format_report(report)

    assert "OOS total return: 0.200000" in text
    assert "OOS volatility: 0.200000" in text
    assert "valid=3/3, evidence=sufficient" in text
    assert "OOS positive-window rate: 3/3=1.000000" in text
    assert "equal_weight_monthly comparison:" in text
    assert "outperformance rate: 3/3=1.000000" in text
    assert "IS/OOS Sharpe generalization gap:" in text
    assert "transitions=1/2" in text
    assert "transition_rate=0.500000" in text
    assert "pass" not in text.lower()
    assert "fail" not in text.lower()
    assert "continuous" not in text.lower()


def _benchmark(
    key: str,
    *,
    total_return: float | None,
    annualized_return: float | None,
    total_return_difference: float | None,
    annualized_return_difference: float | None,
    tracking_error: float | None = None,
    information_ratio: float | None = None,
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
        tracking_error=tracking_error,
        information_ratio=information_ratio,
    )


def _result(
    index: int,
    *,
    best_combo: dict[str, object],
    train_sharpe: float | None = 1.0,
    oos_total_return: float | None = 0.1,
    oos_annualized_return: float | None = 0.1,
    oos_sharpe: float | None = 0.8,
    oos_max_drawdown: float | None = -0.1,
    oos_volatility: float | None = 0.2,
    benchmark_differences: dict[str, tuple[float | None, float | None]] | None = None,
    oos_sortino: float | None = None,
    oos_calmar: float | None = None,
    oos_longest_drawdown_duration_sessions: int | None = None,
    benchmark_active_metrics: dict[str, tuple[float | None, float | None]] | None = None,
) -> WalkForwardWindowResult:
    return WalkForwardWindowResult(
        window=WalkForwardWindow(
            date(2020 + index, 1, 1),
            date(2020 + index, 12, 31),
            date(2021 + index, 1, 1),
            date(2021 + index, 12, 31),
        ),
        best_combo=best_combo,
        oos_version=f"wf-{index:012d}",
        train_sharpe=train_sharpe,
        oos_total_return=oos_total_return,
        oos_annualized_return=oos_annualized_return,
        oos_sharpe=oos_sharpe,
        oos_max_drawdown=oos_max_drawdown,
        oos_volatility=oos_volatility,
        benchmarks=tuple(
            _benchmark(
                key,
                total_return=0.1 if key in (benchmark_differences or {}) else None,
                annualized_return=0.1 if key in (benchmark_differences or {}) else None,
                total_return_difference=total_difference,
                annualized_return_difference=annualized_difference,
                tracking_error=(benchmark_active_metrics or {}).get(key, (None, None))[0],
                information_ratio=(benchmark_active_metrics or {}).get(key, (None, None))[1],
            )
            for key in sorted(
                set(benchmark_differences or {}) | set(benchmark_active_metrics or {})
            )
            for total_difference, annualized_difference in [
                (benchmark_differences or {}).get(key, (None, None))
            ]
        ),
        skipped=[],
        oos_sortino=oos_sortino,
        oos_calmar=oos_calmar,
        oos_longest_drawdown_duration_sessions=oos_longest_drawdown_duration_sessions,
    )
