from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from vela_core.errors import PersistedDataContractError

EvidenceStatus = Literal["sufficient", "insufficient_evidence"]
MINIMUM_EVIDENCE_COUNT = 3
MINIMUM_PUBLICATION_OBSERVATIONS = 100
EVIDENCE_VERSION = "wf_evidence_v1"
EVIDENCE_VERSION_V2 = "wf_evidence_v2"
EVIDENCE_VERSION_V3 = "wf_evidence_v3"
SUPPORTED_EVIDENCE_VERSIONS = (EVIDENCE_VERSION, EVIDENCE_VERSION_V2, EVIDENCE_VERSION_V3)
BenchmarkKey = Literal["equal_weight_monthly", "csi_300_buy_hold"]
TailOwnerKey = Literal["strategy", "equal_weight_monthly", "csi_300_buy_hold"]
TAIL_OWNER_KEYS: tuple[TailOwnerKey, ...] = (
    "strategy",
    "equal_weight_monthly",
    "csi_300_buy_hold",
)


class WalkForwardMetricSummaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    mean: float | None
    median: float | None
    min: float | None
    max: float | None
    std: float | None
    window_count: int = Field(ge=0)
    valid_count: int = Field(ge=0)
    evidence_status: EvidenceStatus

    @model_validator(mode="after")
    def validate_summary_contract(self) -> WalkForwardMetricSummaryModel:
        if self.valid_count > self.window_count:
            raise ValueError("valid_count must not exceed window_count")
        expected_status = (
            "sufficient" if self.valid_count >= MINIMUM_EVIDENCE_COUNT else "insufficient_evidence"
        )
        if self.evidence_status != expected_status:
            raise ValueError("evidence_status must match the minimum-valid-count threshold")
        aggregate_values = (self.mean, self.median, self.min, self.max, self.std)
        if self.valid_count == 0 and any(value is not None for value in aggregate_values):
            raise ValueError("zero-valid metric summaries must contain only null aggregates")
        if self.valid_count > 0 and any(value is None for value in aggregate_values):
            raise ValueError("non-empty metric summaries must contain all aggregate values")
        if self.valid_count > 0:
            assert self.mean is not None
            assert self.median is not None
            assert self.min is not None
            assert self.max is not None
            assert self.std is not None
            if self.min > self.max:
                raise ValueError("metric summary minimum must not exceed maximum")
            if not self.min <= self.mean <= self.max or not self.min <= self.median <= self.max:
                raise ValueError("metric summary mean and median must be within its range")
            if self.std < 0:
                raise ValueError("metric summary population std must be non-negative")
        return self


class WalkForwardRateSummaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    value: float | None
    window_count: int = Field(ge=0)
    valid_count: int = Field(ge=0)
    evidence_status: EvidenceStatus

    @model_validator(mode="after")
    def validate_rate_contract(self) -> WalkForwardRateSummaryModel:
        if self.numerator > self.denominator:
            raise ValueError("rate numerator must not exceed denominator")
        if self.denominator > self.window_count or self.valid_count != self.denominator:
            raise ValueError("rate counts must reconcile with window_count")
        expected_status = (
            "sufficient" if self.valid_count >= MINIMUM_EVIDENCE_COUNT else "insufficient_evidence"
        )
        if self.evidence_status != expected_status:
            raise ValueError("evidence_status must match the minimum-valid-count threshold")
        if self.denominator == 0 and self.value is not None:
            raise ValueError("zero-denominator rates must contain a null value")
        if self.denominator > 0 and self.value is None:
            raise ValueError("non-empty rates must contain a value")
        if self.denominator > 0:
            assert self.value is not None
            expected_value = self.numerator / self.denominator
            if not math.isclose(self.value, expected_value, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError("rate value must equal numerator divided by denominator")
        return self


class WalkForwardParameterStabilityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    value_frequencies: dict[str, int]
    transition_count: int = Field(ge=0)
    comparison_count: int = Field(ge=0)
    transition_rate: float | None

    @model_validator(mode="after")
    def validate_transition_contract(self) -> WalkForwardParameterStabilityModel:
        if not self.value_frequencies or any(
            type(count) is not int or count <= 0 for count in self.value_frequencies.values()
        ):
            raise ValueError("value frequencies must contain positive integer counts")
        maximum_comparisons = max(sum(self.value_frequencies.values()) - 1, 0)
        if self.comparison_count > maximum_comparisons:
            raise ValueError("comparison_count exceeds the available selected values")
        if self.transition_count > self.comparison_count:
            raise ValueError("transition_count must not exceed comparison_count")
        if self.comparison_count == 0 and self.transition_rate is not None:
            raise ValueError("zero-comparison stability must contain a null transition_rate")
        if self.comparison_count > 0 and self.transition_rate is None:
            raise ValueError("non-empty stability must contain a transition_rate")
        if self.comparison_count > 0:
            assert self.transition_rate is not None
            expected_rate = self.transition_count / self.comparison_count
            if not math.isclose(self.transition_rate, expected_rate, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError(
                    "transition_rate must equal transition_count divided by comparison_count"
                )
        return self


class WalkForwardBenchmarkEvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_return_difference: WalkForwardMetricSummaryModel
    annualized_return_difference: WalkForwardMetricSummaryModel
    tracking_error: WalkForwardMetricSummaryModel
    information_ratio: WalkForwardMetricSummaryModel
    outperformance_rate: WalkForwardRateSummaryModel


class WalkForwardStrategyMetricsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_return: WalkForwardMetricSummaryModel
    annualized_return: WalkForwardMetricSummaryModel
    sharpe_ratio: WalkForwardMetricSummaryModel
    max_drawdown: WalkForwardMetricSummaryModel
    volatility: WalkForwardMetricSummaryModel
    sortino_ratio: WalkForwardMetricSummaryModel
    calmar_ratio: WalkForwardMetricSummaryModel
    longest_drawdown_duration_sessions: WalkForwardMetricSummaryModel


class WalkForwardEvidenceV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metrics: WalkForwardStrategyMetricsModel
    positive_window_rate: WalkForwardRateSummaryModel
    generalization_gap: WalkForwardMetricSummaryModel
    benchmarks: dict[BenchmarkKey, WalkForwardBenchmarkEvidenceModel]
    parameter_stability: dict[str, WalkForwardParameterStabilityModel]

    @model_validator(mode="after")
    def validate_benchmarks(self) -> WalkForwardEvidenceV1:
        expected = {"equal_weight_monthly", "csi_300_buy_hold"}
        if set(self.benchmarks) != expected:
            raise ValueError("wf_evidence_v1 requires exactly the two fixed benchmarks")
        return self


class WalkForwardBenchmarkEvidenceV2Model(WalkForwardBenchmarkEvidenceModel):
    capm_alpha: WalkForwardMetricSummaryModel
    capm_beta: WalkForwardMetricSummaryModel
    capm_r_squared: WalkForwardMetricSummaryModel
    up_capture_ratio: WalkForwardMetricSummaryModel
    down_capture_ratio: WalkForwardMetricSummaryModel


class WalkForwardEvidenceV2(WalkForwardEvidenceV1):
    benchmarks: dict[BenchmarkKey, WalkForwardBenchmarkEvidenceV2Model]  # type: ignore[assignment]


class WalkForwardTailDistributionOwnerModel(BaseModel):
    """One owner's distribution evidence for one selected OOS window."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    historical_var_95: float | None
    historical_cvar_95: float | None
    return_skewness: float | None
    return_excess_kurtosis: float | None
    observation_count: int = Field(ge=0)
    tail_observation_count: int = Field(ge=0)
    evidence_status: EvidenceStatus

    @model_validator(mode="after")
    def validate_owner_contract(self) -> WalkForwardTailDistributionOwnerModel:
        expected_tail_count = math.ceil(0.05 * self.observation_count)
        if self.tail_observation_count != expected_tail_count:
            raise ValueError("tail_observation_count must equal ceil(5% of observation_count)")
        expected_status = (
            "sufficient"
            if self.observation_count >= MINIMUM_PUBLICATION_OBSERVATIONS
            else "insufficient_evidence"
        )
        if self.evidence_status != expected_status:
            raise ValueError("evidence_status must match the 100-observation publication threshold")
        if self.observation_count < MINIMUM_PUBLICATION_OBSERVATIONS and any(
            value is not None
            for value in (
                self.historical_var_95,
                self.historical_cvar_95,
                self.return_skewness,
                self.return_excess_kurtosis,
            )
        ):
            raise ValueError("insufficient distribution evidence must contain null metrics")
        if self.historical_var_95 is not None:
            if self.historical_var_95 < 0:
                raise ValueError("Historical VaR must be a non-negative loss magnitude")
            if self.historical_cvar_95 is None or self.historical_cvar_95 < self.historical_var_95:
                raise ValueError("Historical CVaR must be at least Historical VaR")
        return self


class WalkForwardTailDistributionWindowModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ordinal: int = Field(ge=0)
    owners: dict[str, WalkForwardTailDistributionOwnerModel]

    @model_validator(mode="after")
    def validate_owners(self) -> WalkForwardTailDistributionWindowModel:
        if set(self.owners) != set(TAIL_OWNER_KEYS):
            raise ValueError(
                "tail-distribution windows require strategy and both fixed benchmark owners"
            )
        return self


class WalkForwardTailDistributionAggregateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    historical_var_95: WalkForwardMetricSummaryModel
    historical_cvar_95: WalkForwardMetricSummaryModel
    return_skewness: WalkForwardMetricSummaryModel
    return_excess_kurtosis: WalkForwardMetricSummaryModel


class WalkForwardTailDistributionEvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    per_window: tuple[WalkForwardTailDistributionWindowModel, ...]
    aggregates: dict[str, WalkForwardTailDistributionAggregateModel]

    @model_validator(mode="after")
    def validate_aggregate_owners(self) -> WalkForwardTailDistributionEvidenceModel:
        if set(self.aggregates) != set(TAIL_OWNER_KEYS):
            raise ValueError(
                "tail-distribution aggregates require strategy and both fixed benchmark owners"
            )
        return self


class WalkForwardEvidenceV3(WalkForwardEvidenceV2):
    tail_distribution: WalkForwardTailDistributionEvidenceModel


def validate_wf_evidence(
    version: str, document: object
) -> WalkForwardEvidenceV1 | WalkForwardEvidenceV2 | WalkForwardEvidenceV3:
    if version == EVIDENCE_VERSION:
        model_type: (
            type[WalkForwardEvidenceV1] | type[WalkForwardEvidenceV2] | type[WalkForwardEvidenceV3]
        ) = WalkForwardEvidenceV1
    elif version == EVIDENCE_VERSION_V2:
        model_type = WalkForwardEvidenceV2
    elif version == EVIDENCE_VERSION_V3:
        model_type = WalkForwardEvidenceV3
    else:
        raise PersistedDataContractError(f"unsupported Walk-forward evidence version: {version}")
    try:
        return model_type.model_validate(document)
    except Exception as exc:
        raise PersistedDataContractError(
            "invalid persisted Walk-forward evidence document"
        ) from exc


# Stable aliases for callers that prefer the unversioned domain names.
WalkForwardMetricSummary = WalkForwardMetricSummaryModel
WalkForwardRateSummary = WalkForwardRateSummaryModel
WalkForwardParameterStability = WalkForwardParameterStabilityModel
WalkForwardBenchmarkEvidence = WalkForwardBenchmarkEvidenceModel
WalkForwardBenchmarkEvidenceV2 = WalkForwardBenchmarkEvidenceV2Model
WalkForwardEvidence = WalkForwardEvidenceV1
