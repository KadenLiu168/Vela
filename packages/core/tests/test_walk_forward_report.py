from datetime import date

from vela_core.walk_forward.report import WalkForwardReport, WalkForwardWindowResult, format_report
from vela_core.walk_forward.window_splitter import WalkForwardWindow


def test_format_report_includes_aggregate_stability_and_nullable_baseline() -> None:
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
                baseline_annualized_return=None,
                baseline_sharpe=None,
                skipped=[],
            )
        ]
    )

    text = format_report(report)

    assert "2020-01-01 to 2020-12-31" in text
    assert "wf-123456789abc" in text
    assert "Parameter stability" in text
    assert "OOS maximum drawdown" in text
    assert "Baseline comparison" not in text


def test_format_report_keeps_enabled_baseline_visible_when_metrics_are_null() -> None:
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
                baseline_annualized_return=None,
                baseline_sharpe=None,
                skipped=[],
            )
        ],
        baseline_enabled=True,
    )

    text = format_report(report)

    assert "Baseline annualized return difference: n/a; Sharpe difference: n/a" in text
    assert "Baseline comparison" in text
    assert "Annualized return difference mean: n/a (0 windows)" in text
    assert "Sharpe difference mean: n/a (0 windows)" in text


def test_report_summarizes_skips_and_baseline_differences() -> None:
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
                0.1,
                0.5,
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
                None,
                None,
                [],
            ),
        ],
        baseline_enabled=True,
    )

    assert report.baseline_differences() == {
        "annualized_return_mean": 0.1,
        "annualized_return_count": 1,
        "sharpe_mean": 0.30000000000000004,
        "sharpe_count": 1,
    }
    text = format_report(report)
    assert "Skip summary: unscorable result (1)" in text
    assert "Baseline comparison" in text
    assert "parameters.selection.top_n: window 1=1, window 2=2" in text
