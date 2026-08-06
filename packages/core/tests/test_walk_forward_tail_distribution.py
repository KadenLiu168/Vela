# ruff: noqa: E501

from __future__ import annotations

import math
from copy import deepcopy
from datetime import date
from decimal import Decimal
from statistics import mean, median, pstdev

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from vela_core.models import BacktestBenchmark, BacktestRun, Base
from vela_core.walk_forward.evidence import (
    EVIDENCE_VERSION,
    EVIDENCE_VERSION_V2,
    EVIDENCE_VERSION_V3,
    PersistedDataContractError,
    WalkForwardEvidenceV3,
    validate_wf_evidence,
)
from vela_core.walk_forward.report import (
    WalkForwardBenchmarkResult,
    WalkForwardReport,
    WalkForwardWindowResult,
    format_report,
)
from vela_core.walk_forward.tail_evidence_validation import (
    validate_v3_tail_source_evidence,
)
from vela_core.walk_forward.window_splitter import WalkForwardWindow

EQ = "equal_weight_monthly"
CSI = "csi_300_buy_hold"
TAIL_METRICS = (
    "historical_var_95",
    "historical_cvar_95",
    "return_skewness",
    "return_excess_kurtosis",
)


def _benchmark(
    key: str,
    *,
    var: float | None,
    cvar: float | None,
    skew: float | None,
    kurt: float | None,
    observations: int,
) -> WalkForwardBenchmarkResult:
    return WalkForwardBenchmarkResult(
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
        historical_var_95=var,
        historical_cvar_95=cvar,
        return_skewness=skew,
        return_excess_kurtosis=kurt,
        distribution_observation_count=observations,
        tail_observation_count=math.ceil(0.05 * observations),
    )


def _window(
    index: int,
    *,
    strategy: tuple[float | None, float | None, float | None, float | None, int],
    equal_weight: tuple[float | None, float | None, float | None, float | None, int],
    csi_300: tuple[float | None, float | None, float | None, float | None, int],
) -> WalkForwardWindowResult:
    strategy_var, strategy_cvar, strategy_skew, strategy_kurt, strategy_obs = strategy
    equal_var, equal_cvar, equal_skew, equal_kurt, equal_obs = equal_weight
    csi_var, csi_cvar, csi_skew, csi_kurt, csi_obs = csi_300
    return WalkForwardWindowResult(
        window=WalkForwardWindow(
            date(2020 + index, 1, 1),
            date(2020 + index, 12, 31),
            date(2021 + index, 1, 1),
            date(2021 + index, 12, 31),
        ),
        best_combo={"parameters.selection.top_n": index},
        oos_version=f"wf-{index:012d}",
        train_sharpe=1.0,
        oos_total_return=0.1,
        oos_annualized_return=0.1,
        oos_sharpe=0.8,
        oos_max_drawdown=-0.1,
        oos_volatility=0.2,
        benchmarks=(
            _benchmark(
                EQ,
                var=equal_var,
                cvar=equal_cvar,
                skew=equal_skew,
                kurt=equal_kurt,
                observations=equal_obs,
            ),
            _benchmark(
                CSI,
                var=csi_var,
                cvar=csi_cvar,
                skew=csi_skew,
                kurt=csi_kurt,
                observations=csi_obs,
            ),
        ),
        skipped=[],
        historical_var_95=strategy_var,
        historical_cvar_95=strategy_cvar,
        return_skewness=strategy_skew,
        return_excess_kurtosis=strategy_kurt,
        distribution_observation_count=strategy_obs,
        tail_observation_count=math.ceil(0.05 * strategy_obs),
    )


def _report() -> WalkForwardReport:
    return WalkForwardReport(
        [
            _window(
                0,
                strategy=(0.02, 0.06, 0.1, 0.2, 100),
                equal_weight=(0.01, 0.03, -0.1, 0.1, 100),
                csi_300=(0.04, 0.08, 0.2, -0.3, 100),
            ),
            _window(
                1,
                strategy=(None, None, None, None, 99),
                equal_weight=(0.0, 0.0, None, None, 100),
                csi_300=(0.04, 0.08, 0.2, -0.3, 100),
            ),
            _window(
                2,
                strategy=(0.03, 0.05, 0.0, -0.1, 101),
                equal_weight=(0.01, 0.03, -0.1, 0.1, 100),
                csi_300=(0.05, 0.09, 0.3, -0.4, 100),
            ),
        ]
    )


# --- 3.1 per-window report evidence ---


def test_report_retains_per_window_owner_distribution_evidence() -> None:
    document = _report().evidence_document()
    assert document.tail_distribution.per_window
    assert [window.ordinal for window in document.tail_distribution.per_window] == [0, 1, 2]
    for window in document.tail_distribution.per_window:
        assert set(window.owners) == {"strategy", EQ, CSI}
    first = document.tail_distribution.per_window[0]
    assert first.owners["strategy"].historical_var_95 == 0.02
    assert first.owners["strategy"].historical_cvar_95 == 0.06
    assert first.owners["strategy"].return_skewness == 0.1
    assert first.owners["strategy"].return_excess_kurtosis == 0.2
    assert first.owners["strategy"].observation_count == 100
    assert first.owners["strategy"].tail_observation_count == 5
    assert first.owners["strategy"].evidence_status == "sufficient"
    assert first.owners[EQ].historical_var_95 == 0.01
    assert first.owners[CSI].historical_var_95 == 0.04
    assert first.owners[CSI].historical_cvar_95 == 0.08


def test_report_keeps_null_metrics_with_counts_and_zero_losses() -> None:
    document = _report().evidence_document()
    second = document.tail_distribution.per_window[1]
    strategy = second.owners["strategy"]
    assert strategy.historical_var_95 is None
    assert strategy.historical_cvar_95 is None
    assert strategy.return_skewness is None
    assert strategy.return_excess_kurtosis is None
    assert strategy.observation_count == 99
    assert strategy.tail_observation_count == 5
    assert strategy.evidence_status == "insufficient_evidence"
    equal_weight = second.owners[EQ]
    # Constant distribution: valid zero losses with null shape statistics.
    assert equal_weight.historical_var_95 == 0.0
    assert equal_weight.historical_cvar_95 == 0.0
    assert equal_weight.return_skewness is None
    assert equal_weight.return_excess_kurtosis is None
    assert equal_weight.evidence_status == "sufficient"


def test_terminal_report_shows_per_window_distribution_lines() -> None:
    report = format_report(_report())
    # One line per strategy owner plus one per benchmark owner, across 3 windows.
    assert report.count("Distribution (1D historical loss; positive losses):") == 9
    assert "VaR95=0.020000" in report
    assert "VaR95=n/a" in report
    assert "observations=99" in report
    assert "VaR95=0.000000" in report


def test_stitched_oos_curve_creates_no_parent_distribution() -> None:
    document = _report().evidence_document()
    assert set(document.tail_distribution.model_dump()) == {"per_window", "aggregates"}
    report = format_report(_report())
    assert "stitched" not in report.lower()


# --- 3.2 aggregation semantics ---


def test_tail_aggregates_are_descriptive_across_windows() -> None:
    document = _report().evidence_document()
    strategy_var = document.tail_distribution.aggregates["strategy"].historical_var_95
    values = [0.02, 0.03]
    assert strategy_var.mean == mean(values)
    assert strategy_var.median == median(values)
    assert strategy_var.min == min(values)
    assert strategy_var.max == max(values)
    assert strategy_var.std == pstdev(values)
    assert strategy_var.window_count == 3
    assert strategy_var.valid_count == 2
    assert strategy_var.evidence_status == "insufficient_evidence"


def test_tail_aggregates_drop_nulls_and_keep_valid_zeros() -> None:
    document = _report().evidence_document()
    equal_weight_var = document.tail_distribution.aggregates[EQ].historical_var_95
    values = [0.01, 0.0, 0.01]
    assert equal_weight_var.valid_count == 3
    assert equal_weight_var.mean == mean(values)
    assert equal_weight_var.evidence_status == "sufficient"
    equal_weight_kurt = document.tail_distribution.aggregates[EQ].return_excess_kurtosis
    assert equal_weight_kurt.valid_count == 2
    assert equal_weight_kurt.window_count == 3
    assert equal_weight_kurt.evidence_status == "insufficient_evidence"
    assert equal_weight_kurt.min == 0.1


def test_aggregate_labels_avoid_best_worst_and_pass_fail_language() -> None:
    report = format_report(_report())
    tail_section = report.split("Tail-distribution aggregates", 1)[1]
    assert "worst" not in tail_section
    assert "best" not in tail_section
    assert "pass" not in tail_section.lower()
    assert "fail" not in tail_section.lower()


# --- 3.3/3.4 strict v3 validation and corruption rejection ---


def _v3_document() -> dict[str, object]:
    return _report().evidence_document().model_dump(mode="json")


def test_v3_document_round_trips_and_extends_v2() -> None:
    document = _v3_document()
    evidence = validate_wf_evidence(EVIDENCE_VERSION_V3, document)
    assert isinstance(evidence, WalkForwardEvidenceV3)
    round_tripped = validate_wf_evidence(EVIDENCE_VERSION_V3, evidence.model_dump(mode="json"))
    assert isinstance(round_tripped, WalkForwardEvidenceV3)
    assert round_tripped.model_dump(mode="json") == document


def test_v3_rejects_unsupported_version() -> None:
    with pytest.raises(PersistedDataContractError, match="unsupported"):
        validate_wf_evidence("wf_evidence_v9", _v3_document())


def test_v3_rejects_missing_owner() -> None:
    document = deepcopy(_v3_document())
    del document["tail_distribution"]["per_window"][0]["owners"]["strategy"]
    with pytest.raises((ValidationError, PersistedDataContractError)):
        validate_wf_evidence(EVIDENCE_VERSION_V3, document)


def test_v3_rejects_unknown_owner() -> None:
    document = deepcopy(_v3_document())
    document["tail_distribution"]["per_window"][0]["owners"]["other_owner"] = deepcopy(
        document["tail_distribution"]["per_window"][0]["owners"]["strategy"]
    )
    with pytest.raises((ValidationError, PersistedDataContractError)):
        validate_wf_evidence(EVIDENCE_VERSION_V3, document)


def test_v3_rejects_wrong_tail_count_relationship() -> None:
    document = deepcopy(_v3_document())
    document["tail_distribution"]["per_window"][0]["owners"]["strategy"][
        "tail_observation_count"
    ] = 6
    with pytest.raises(PersistedDataContractError, match="invalid persisted"):
        validate_wf_evidence(EVIDENCE_VERSION_V3, document)


def test_v3_rejects_non_finite_value() -> None:
    document = deepcopy(_v3_document())
    document["tail_distribution"]["per_window"][0]["owners"]["strategy"]["historical_cvar_95"] = (
        float("inf")
    )
    with pytest.raises((ValidationError, PersistedDataContractError)):
        validate_wf_evidence(EVIDENCE_VERSION_V3, document)


def test_v3_rejects_loss_invariant_violation() -> None:
    document = deepcopy(_v3_document())
    document["tail_distribution"]["per_window"][0]["owners"]["strategy"]["historical_var_95"] = 0.5
    with pytest.raises((ValidationError, PersistedDataContractError)):
        validate_wf_evidence(EVIDENCE_VERSION_V3, document)


def test_v3_source_validation_rejects_value_mismatch() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        oos_rows = _seed_source_rows(session, count=3)
        evidence = validate_wf_evidence(EVIDENCE_VERSION_V3, _v3_document())
        assert isinstance(evidence, WalkForwardEvidenceV3)
        validate_v3_tail_source_evidence(oos_rows, evidence)

        oos_rows[0].historical_var_95 = Decimal("0.999")
        with pytest.raises(PersistedDataContractError, match="does not match its source"):
            validate_v3_tail_source_evidence(oos_rows, evidence)


def test_v3_source_validation_rejects_missing_metric_version() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        oos_rows = _seed_source_rows(session, count=3)
        oos_rows[
            0
        ].parameters_json = '{"benchmark_regime_metric_version":"benchmark_regime_metrics_v1"}'
        evidence = validate_wf_evidence(EVIDENCE_VERSION_V3, _v3_document())
        assert isinstance(evidence, WalkForwardEvidenceV3)
        with pytest.raises(PersistedDataContractError, match="metric version"):
            validate_v3_tail_source_evidence(oos_rows, evidence)


def test_v3_source_validation_rejects_wrong_observation_count() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        oos_rows = _seed_source_rows(session, count=3)
        oos_rows[1].distribution_observation_count = 50
        oos_rows[1].tail_observation_count = 3
        evidence = validate_wf_evidence(EVIDENCE_VERSION_V3, _v3_document())
        assert isinstance(evidence, WalkForwardEvidenceV3)
        with pytest.raises(PersistedDataContractError, match="does not match its source"):
            validate_v3_tail_source_evidence(oos_rows, evidence)


def test_legacy_v1_and_v2_documents_remain_readable() -> None:
    v3 = _v3_document()
    v2 = deepcopy(v3)
    v2.pop("tail_distribution")
    assert validate_wf_evidence(EVIDENCE_VERSION_V2, v2) is not None
    v1 = deepcopy(v2)
    for key in (EQ, CSI):
        v1["benchmarks"][key] = {
            name: v1["benchmarks"][key][name]
            for name in (
                "total_return_difference",
                "annualized_return_difference",
                "tracking_error",
                "information_ratio",
                "outperformance_rate",
            )
        }
    assert validate_wf_evidence(EVIDENCE_VERSION, v1) is not None
    assert "tail_distribution" not in v1
    assert "capm_alpha" not in v1["benchmarks"][CSI]


def _seed_source_rows(session: object, *, count: int) -> list[BacktestRun]:
    rows: list[BacktestRun] = []
    for index in range(count):
        run = BacktestRun(
            strategy_id="demo",
            config_version=f"wf-{index:012d}",
            start_date=date(2021 + index, 1, 1),
            end_date=date(2021 + index, 12, 31),
            parameters_json=(
                '{"benchmark_regime_metric_version":"benchmark_regime_metrics_v1",'
                '"tail_distribution_metric_version":"tail_distribution_metrics_v1"}'
            ),
            started_at=date(2021 + index, 1, 1),
            status="success",
            distribution_observation_count=100 if index != 1 else 99,
            tail_observation_count=math.ceil(0.05 * (100 if index != 1 else 99)),
        )
        if index == 2:
            run.distribution_observation_count = 101
            run.tail_observation_count = math.ceil(0.05 * 101)
        if index == 0:
            run.historical_var_95 = Decimal("0.02")
            run.historical_cvar_95 = Decimal("0.06")
            run.return_skewness = Decimal("0.1")
            run.return_excess_kurtosis = Decimal("0.2")
        elif index == 2:
            run.historical_var_95 = Decimal("0.03")
            run.historical_cvar_95 = Decimal("0.05")
            run.return_skewness = Decimal("0.0")
            run.return_excess_kurtosis = Decimal("-0.1")
        run.benchmarks.extend(
            [
                BacktestBenchmark(
                    benchmark_key=key,
                    display_name=key,
                    capm_alpha=Decimal("0.1") if key == CSI else None,
                    capm_beta=Decimal("0.1") if key == CSI else None,
                    capm_r_squared=Decimal("0.1") if key == CSI else None,
                    capm_observation_count=2 if key == CSI else None,
                    up_capture_ratio=Decimal("0.1"),
                    up_capture_observation_count=1,
                    down_capture_ratio=Decimal("0.1"),
                    down_capture_observation_count=1,
                    historical_var_95=(
                        Decimal("0.0")
                        if key == EQ and index == 1
                        else Decimal("0.01")
                        if key == EQ
                        else Decimal("0.04")
                        if index != 2
                        else Decimal("0.05")
                    ),
                    historical_cvar_95=(
                        Decimal("0.0")
                        if key == EQ and index == 1
                        else Decimal("0.03")
                        if key == EQ
                        else Decimal("0.08")
                        if index != 2
                        else Decimal("0.09")
                    ),
                    return_skewness=(
                        None
                        if key == EQ and index == 1
                        else Decimal("-0.1")
                        if key == EQ
                        else Decimal("0.2")
                        if index != 2
                        else Decimal("0.3")
                    ),
                    return_excess_kurtosis=(
                        None
                        if key == EQ and index == 1
                        else Decimal("0.1")
                        if key == EQ
                        else Decimal("-0.3")
                        if index != 2
                        else Decimal("-0.4")
                    ),
                    distribution_observation_count=100,
                    tail_observation_count=5,
                )
                for key in (EQ, CSI)
            ]
        )
        session.add(run)  # type: ignore[attr-defined]
        session.flush()  # type: ignore[attr-defined]
        rows.append(run)
    return rows
