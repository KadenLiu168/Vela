from __future__ import annotations

from datetime import date

from vela_core.walk_forward.evidence import WalkForwardEvidenceV1
from vela_core.walk_forward.report import (
    WalkForwardBenchmarkResult,
    WalkForwardReport,
    WalkForwardWindowResult,
)
from vela_core.walk_forward.window_splitter import WalkForwardWindow


def test_report_serializes_the_prerequisite_evidence_and_window_audit() -> None:
    windows = []
    for ordinal in range(3):
        window = WalkForwardWindow(
            train_start=date(2020 + ordinal, 1, 1),
            train_end=date(2020 + ordinal, 12, 31),
            test_start=date(2021 + ordinal, 1, 1),
            test_end=date(2021 + ordinal, 12, 31),
        )
        benchmarks = tuple(
            WalkForwardBenchmarkResult(
                key=key,
                name=key,
                total_return=0.1,
                annualized_return=0.1,
                max_drawdown=-0.1,
                volatility=0.1,
                sharpe_ratio=1.0,
                total_return_difference=0.02,
                annualized_return_difference=0.01,
                tracking_error=0.03,
                information_ratio=0.4,
                capm_alpha=0.5 if key == "csi_300_buy_hold" else None,
                capm_beta=1.1 if key == "csi_300_buy_hold" else None,
                capm_r_squared=0.8 if key == "csi_300_buy_hold" else None,
                capm_observation_count=240 if key == "csi_300_buy_hold" else None,
                up_capture_ratio=1.2,
                up_capture_observation_count=9,
                down_capture_ratio=0.7,
                down_capture_observation_count=4,
            )
            for key in ("equal_weight_monthly", "csi_300_buy_hold")
        )
        windows.append(
            WalkForwardWindowResult(
                window=window,
                best_combo={"parameters.selection.top_n": 1},
                oos_version="wf-000000000001",
                train_sharpe=1.1,
                oos_total_return=0.1,
                oos_annualized_return=0.1,
                oos_sharpe=1.0,
                oos_max_drawdown=-0.1,
                oos_volatility=0.1,
                benchmarks=benchmarks,
                skipped=[],
                oos_backtest_id=ordinal + 1,
                candidate_count=1,
                eligible_count=1,
                skipped_count=0,
                skip_reason_counts={},
            )
        )

    evidence = WalkForwardReport(windows).evidence_document()

    assert isinstance(evidence, WalkForwardEvidenceV1)
    assert set(evidence.metrics.model_dump()) == {
        "total_return",
        "annualized_return",
        "sharpe_ratio",
        "max_drawdown",
        "volatility",
        "sortino_ratio",
        "calmar_ratio",
        "longest_drawdown_duration_sessions",
    }
    assert evidence.benchmarks["equal_weight_monthly"].tracking_error.valid_count == 3
