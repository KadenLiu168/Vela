from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError
from vela_core.walk_forward.evidence import (
    PersistedDataContractError,
    WalkForwardEvidenceV1,
    validate_wf_evidence,
)


def _summary() -> dict[str, object]:
    return {
        "mean": 0.1,
        "median": 0.1,
        "min": 0.05,
        "max": 0.15,
        "std": 0.04,
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }


def _rate() -> dict[str, object]:
    return {
        "numerator": 2,
        "denominator": 3,
        "value": 2 / 3,
        "window_count": 3,
        "valid_count": 3,
        "evidence_status": "sufficient",
    }


def _document() -> dict[str, object]:
    metrics = {
        name: _summary()
        for name in (
            "total_return",
            "annualized_return",
            "sharpe_ratio",
            "max_drawdown",
            "volatility",
            "sortino_ratio",
            "calmar_ratio",
            "longest_drawdown_duration_sessions",
        )
    }
    return {
        "metrics": metrics,
        "positive_window_rate": _rate(),
        "generalization_gap": _summary(),
        "benchmarks": {
            key: {
                "total_return_difference": _summary(),
                "annualized_return_difference": _summary(),
                "tracking_error": _summary(),
                "information_ratio": _summary(),
                "outperformance_rate": _rate(),
            }
            for key in ("equal_weight_monthly", "csi_300_buy_hold")
        },
        "parameter_stability": {
            "parameters.selection.top_n": {
                "value_frequencies": {"1": 2, "2": 1},
                "transition_count": 1,
                "comparison_count": 2,
                "transition_rate": 0.5,
            }
        },
    }


def test_wf_evidence_v1_round_trips_all_strategy_and_benchmark_summaries() -> None:
    evidence = WalkForwardEvidenceV1.model_validate(_document())

    dumped = evidence.model_dump(mode="json")

    assert set(dumped["metrics"]) == {
        "total_return",
        "annualized_return",
        "sharpe_ratio",
        "max_drawdown",
        "volatility",
        "sortino_ratio",
        "calmar_ratio",
        "longest_drawdown_duration_sessions",
    }
    assert set(dumped["benchmarks"]) == {"equal_weight_monthly", "csi_300_buy_hold"}
    assert dumped["positive_window_rate"]["numerator"] == 2
    assert dumped["generalization_gap"]["valid_count"] == 3
    assert dumped["parameter_stability"]["parameters.selection.top_n"]["transition_count"] == 1


@pytest.mark.parametrize("field", ["total_return", "tracking_error", "information_ratio"])
def test_wf_evidence_v1_keeps_metric_local_nulls_and_threshold_status(field: str) -> None:
    document = _document()
    if field == "total_return":
        target = document["metrics"][field]
    else:
        target = document["benchmarks"]["equal_weight_monthly"][field]
    target.update(
        mean=None,
        median=None,
        min=None,
        max=None,
        std=None,
        valid_count=0,
        evidence_status="insufficient_evidence",
    )

    evidence = WalkForwardEvidenceV1.model_validate(document)

    assert evidence.model_dump(mode="json")["metrics"]["sharpe_ratio"]["valid_count"] == 3
    if field == "total_return":
        assert evidence.metrics.total_return.evidence_status == "insufficient_evidence"
    else:
        assert (
            evidence.benchmarks["equal_weight_monthly"].model_dump()[field]["evidence_status"]
            == "insufficient_evidence"
        )


def test_wf_evidence_v1_rejects_missing_extra_and_non_finite_fields() -> None:
    missing = deepcopy(_document())
    del missing["metrics"]["volatility"]
    with pytest.raises(ValidationError):
        WalkForwardEvidenceV1.model_validate(missing)

    extra = deepcopy(_document())
    extra["unexpected"] = True
    with pytest.raises(ValidationError):
        WalkForwardEvidenceV1.model_validate(extra)

    non_finite = deepcopy(_document())
    non_finite["metrics"]["sharpe_ratio"]["mean"] = float("nan")
    with pytest.raises(ValidationError):
        WalkForwardEvidenceV1.model_validate(non_finite)


def test_wf_evidence_v1_requires_threshold_status_to_match_valid_count() -> None:
    document = _document()
    document["metrics"]["sharpe_ratio"]["valid_count"] = 2

    with pytest.raises(ValidationError):
        WalkForwardEvidenceV1.model_validate(document)


def test_wf_evidence_v1_rejects_unreconciled_derived_values() -> None:
    rate = _document()
    rate["positive_window_rate"]["value"] = 0.5
    with pytest.raises(ValidationError):
        WalkForwardEvidenceV1.model_validate(rate)

    transition = _document()
    transition["parameter_stability"]["parameters.selection.top_n"]["transition_rate"] = 0.25
    with pytest.raises(ValidationError):
        WalkForwardEvidenceV1.model_validate(transition)

    frequencies = _document()
    frequencies["parameter_stability"]["parameters.selection.top_n"]["value_frequencies"] = {
        "1": 0,
        "2": 3,
    }
    with pytest.raises(ValidationError):
        WalkForwardEvidenceV1.model_validate(frequencies)

    negative_std = _document()
    negative_std["metrics"]["total_return"]["std"] = -0.1
    with pytest.raises(ValidationError):
        WalkForwardEvidenceV1.model_validate(negative_std)

    out_of_range_mean = _document()
    out_of_range_mean["metrics"]["total_return"]["mean"] = 0.2
    with pytest.raises(ValidationError):
        WalkForwardEvidenceV1.model_validate(out_of_range_mean)


def test_persisted_evidence_validation_fails_closed_for_version_and_document_drift() -> None:
    with pytest.raises(PersistedDataContractError, match="unsupported"):
        validate_wf_evidence("wf_evidence_v0", _document())

    corrupt = _document()
    corrupt["metrics"]["sharpe_ratio"]["valid_count"] = 99
    with pytest.raises(PersistedDataContractError, match="invalid"):
        validate_wf_evidence("wf_evidence_v1", corrupt)
