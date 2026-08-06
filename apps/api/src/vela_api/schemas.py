from datetime import date, datetime
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict
from typing_extensions import TypeAliasType
from vela_core.config import ETFConfig
from vela_core.strategy_config import StrategyConfig


class ResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


JsonValue = TypeAliasType(  # type: ignore[misc]
    "JsonValue",
    None
    | bool
    | int
    | float
    | str
    | list["JsonValue"]  # type: ignore[misc]
    | dict[str, "JsonValue"],  # type: ignore[misc]
)  # type: ignore[misc]
JsonObject: TypeAlias = dict[str, JsonValue]  # type: ignore[misc]


class HealthResponse(ResponseModel):
    status: str


class ConfigResponse(ResponseModel):
    strategy: StrategyConfig
    etf_pool: "EtfPoolResponse"


class EtfPoolResponse(ResponseModel):
    pool_id: str
    version: int
    description: str | None
    provider: str
    currency: str
    total_etfs: int
    active_etfs: int
    etfs: list[ETFConfig]


class DashboardMarketDataEtfResponse(ResponseModel):
    etf_id: int
    exchange: str
    symbol: str
    name: str
    category: str | None
    earliest_trade_date: date | None


class DashboardMarketDataResponse(ResponseModel):
    price_rows: int
    covered_etfs: int
    earliest_trade_date: date | None
    latest_trade_date: date | None
    etf_list: list[DashboardMarketDataEtfResponse]


class DashboardSignalResponse(ResponseModel):
    signal_id: int
    signal_date: date
    config_version: str
    status: str
    result: str | None
    generated_at: datetime
    is_fallback: bool
    position_count: int


class DashboardBacktestResponse(ResponseModel):
    run_id: int
    strategy_id: str
    config_version: str
    start_date: date
    end_date: date
    status: str
    total_return: str | None
    max_drawdown: str | None
    sharpe_ratio: str | None
    started_at: datetime


class DashboardFetchLogResponse(ResponseModel):
    fetch_log_id: int
    fetch_time: datetime
    mode: str
    status: str
    rows_fetched: int | None
    rows_inserted: int | None
    rows_updated: int | None
    error_summary: str | None


class DashboardResponse(ResponseModel):
    strategy: StrategyConfig
    market_data: DashboardMarketDataResponse
    latest_signal: DashboardSignalResponse | None
    recent_backtest: DashboardBacktestResponse | None
    recent_fetch_logs: list[DashboardFetchLogResponse]


class EtfResponse(ResponseModel):
    id: int
    exchange: str
    symbol: str
    name: str


class EtfPricePointResponse(ResponseModel):
    trade_date: date
    price: str


class EtfPriceTrendResponse(ResponseModel):
    etf: EtfResponse
    points: list[EtfPricePointResponse]


class MarketDataFetchResponse(ResponseModel):
    status: str
    requested_etf_count: int
    rows_fetched: int
    rows_inserted: int
    rows_updated: int
    failed_symbols: list[str]
    error_message: str | None


class BootstrapStepResponse(ResponseModel):
    name: str
    status: str
    duration_seconds: float
    error_message: str | None


class BootstrapResponse(ResponseModel):
    status: str
    failed_step: str | None
    total_duration_seconds: float
    steps: list[BootstrapStepResponse]


class GeneratedPositionResponse(ResponseModel):
    etf_id: int
    exchange: str
    symbol: str
    target_weight: str | None
    rank: int | None
    score: str | None


class GenerateSignalResponse(ResponseModel):
    signal_id: int
    signal_date: date
    config_version: str
    status: str
    result: str | None
    error_message: str | None
    source: str
    positions: list[GeneratedPositionResponse]


class SignalMetadataResponse(ResponseModel):
    signal_id: int
    signal_date: date
    config_version: str
    generated_at: datetime
    result: str
    is_fallback: bool


class SignalPositionResponse(ResponseModel):
    exchange: str
    symbol: str
    name: str
    target_weight: str | None
    rank: int | None
    score: str | None
    is_fallback: bool


class LatestSignalResponse(ResponseModel):
    has_signal: bool
    signal: SignalMetadataResponse | None
    positions: list[SignalPositionResponse]


class SignalListItemResponse(ResponseModel):
    signal_id: int
    signal_date: date
    config_version: str
    result: str
    generated_at: datetime
    is_fallback: bool
    position_count: int
    source: str
    backtest_run_id: int | None


class SignalListResponse(ResponseModel):
    signals: list[SignalListItemResponse]


class SignalDetailMetadataResponse(SignalMetadataResponse):
    strategy_id: str
    source: str
    backtest_run_id: int | None


class SignalDetailResponse(ResponseModel):
    signal: SignalDetailMetadataResponse
    positions: list[SignalPositionResponse]


class BacktestMetricsResponse(ResponseModel):
    total_return: str | None
    annualized_return: str | None
    max_drawdown: str | None
    volatility: str | None
    sharpe_ratio: str | None
    sortino_ratio: str | None
    calmar_ratio: str | None
    longest_drawdown_duration_sessions: int | None
    longest_drawdown_peak_date: date | None
    longest_drawdown_trough_date: date | None
    longest_drawdown_recovery_date: date | None


class BacktestRunResponse(BacktestMetricsResponse):
    run_id: int
    status: str
    start_date: date
    end_date: date
    trading_day_count: int
    signal_count: int
    benchmarks: list["BacktestBenchmarkResponse"]


class BacktestListItemResponse(ResponseModel):
    run_id: int
    strategy_id: str
    config_version: str
    start_date: date
    end_date: date
    status: str
    started_at: datetime
    finished_at: datetime | None
    total_return: str | None
    annualized_return: str | None
    max_drawdown: str | None
    volatility: str | None
    sharpe_ratio: str | None


class BacktestListResponse(ResponseModel):
    runs: list[BacktestListItemResponse]


class BacktestDetailRunResponse(ResponseModel):
    run_id: int
    strategy_id: str
    config_version: str
    start_date: date
    end_date: date
    parameters_json: str
    status: str
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class EquityCurvePointResponse(ResponseModel):
    trade_date: date
    net_value: str | None
    cash: str | None
    market_value: str | None
    total_assets: str | None
    positions_json: str


class BacktestBenchmarkCurvePointResponse(ResponseModel):
    trade_date: date
    net_value: str


class BacktestBenchmarkResponse(BacktestMetricsResponse):
    key: str
    name: str
    total_return_difference: str | None
    annualized_return_difference: str | None
    tracking_error: str | None
    information_ratio: str | None
    capm_alpha: str | None
    capm_beta: str | None
    capm_r_squared: str | None
    capm_observation_count: int | None
    up_capture_ratio: str | None
    up_capture_observation_count: int | None
    down_capture_ratio: str | None
    down_capture_observation_count: int | None
    equity_curve: list[BacktestBenchmarkCurvePointResponse] = []


class ReturnStabilityRollingPointResponse(ResponseModel):
    window_start_date: date
    trade_date: date
    total_return: str
    volatility: str
    sharpe_ratio: str | None


class ReturnStabilityCalendarBucketResponse(ResponseModel):
    period: str
    first_date: date
    last_date: date
    observation_count: int
    total_return: str
    is_partial: bool


class ReturnStabilityEntityResponse(ResponseModel):
    window_sessions: int
    rolling_status: str
    sharpe_status: str
    source_point_count: int
    effective_return_count: int
    rolling: list[ReturnStabilityRollingPointResponse]
    monthly: list[ReturnStabilityCalendarBucketResponse]
    yearly: list[ReturnStabilityCalendarBucketResponse]


class ReturnStabilityBenchmarkResponse(ReturnStabilityEntityResponse):
    key: str
    name: str


class ReturnStabilityResponse(ResponseModel):
    strategy: ReturnStabilityEntityResponse
    benchmarks: list[ReturnStabilityBenchmarkResponse]


class BacktestDetailResponse(ResponseModel):
    run: BacktestDetailRunResponse
    metrics: BacktestMetricsResponse
    equity_curve: list[EquityCurvePointResponse]
    signal_ids: list[int]
    signal_count: int
    benchmarks: list[BacktestBenchmarkResponse]
    return_stability: ReturnStabilityResponse


class BacktestSignalSummaryResponse(ResponseModel):
    signal_id: int
    signal_date: date
    result: str
    backtest_run_id: int


class BacktestSignalsResponse(ResponseModel):
    signals: list[BacktestSignalSummaryResponse]


class WalkForwardMetricSummaryResponse(ResponseModel):
    mean: float | None
    median: float | None
    min: float | None
    max: float | None
    std: float | None
    window_count: int
    valid_count: int
    evidence_status: Literal["sufficient", "insufficient_evidence"]


class WalkForwardRateSummaryResponse(ResponseModel):
    numerator: int
    denominator: int
    value: float | None
    window_count: int
    valid_count: int
    evidence_status: Literal["sufficient", "insufficient_evidence"]


class WalkForwardParameterStabilityResponse(ResponseModel):
    value_frequencies: dict[str, int]
    transition_count: int
    comparison_count: int
    transition_rate: float | None


class WalkForwardBenchmarkEvidenceResponse(ResponseModel):
    total_return_difference: WalkForwardMetricSummaryResponse
    annualized_return_difference: WalkForwardMetricSummaryResponse
    tracking_error: WalkForwardMetricSummaryResponse
    information_ratio: WalkForwardMetricSummaryResponse
    outperformance_rate: WalkForwardRateSummaryResponse


class WalkForwardBenchmarkEvidenceV2Response(WalkForwardBenchmarkEvidenceResponse):
    capm_alpha: WalkForwardMetricSummaryResponse
    capm_beta: WalkForwardMetricSummaryResponse
    capm_r_squared: WalkForwardMetricSummaryResponse
    up_capture_ratio: WalkForwardMetricSummaryResponse
    down_capture_ratio: WalkForwardMetricSummaryResponse


class WalkForwardStrategyMetricsResponse(ResponseModel):
    total_return: WalkForwardMetricSummaryResponse
    annualized_return: WalkForwardMetricSummaryResponse
    sharpe_ratio: WalkForwardMetricSummaryResponse
    max_drawdown: WalkForwardMetricSummaryResponse
    volatility: WalkForwardMetricSummaryResponse
    sortino_ratio: WalkForwardMetricSummaryResponse
    calmar_ratio: WalkForwardMetricSummaryResponse
    longest_drawdown_duration_sessions: WalkForwardMetricSummaryResponse


class WalkForwardBenchmarkEvidenceMapResponse(ResponseModel):
    equal_weight_monthly: WalkForwardBenchmarkEvidenceResponse
    csi_300_buy_hold: WalkForwardBenchmarkEvidenceResponse


class WalkForwardEvidenceResponse(ResponseModel):
    metrics: WalkForwardStrategyMetricsResponse
    positive_window_rate: WalkForwardRateSummaryResponse
    generalization_gap: WalkForwardMetricSummaryResponse
    benchmarks: WalkForwardBenchmarkEvidenceMapResponse
    parameter_stability: dict[str, WalkForwardParameterStabilityResponse]


class WalkForwardBenchmarkEvidenceV2MapResponse(ResponseModel):
    equal_weight_monthly: WalkForwardBenchmarkEvidenceV2Response
    csi_300_buy_hold: WalkForwardBenchmarkEvidenceV2Response


class WalkForwardEvidenceV2Response(WalkForwardEvidenceResponse):
    benchmarks: WalkForwardBenchmarkEvidenceV2MapResponse  # type: ignore[assignment]


class WalkForwardRunSummaryResponse(ResponseModel):
    run_id: int
    strategy_id: str
    start_date: date
    end_date: date
    window_count: int
    provenance_version: str
    evidence_version: str
    config_checksum: str
    input_data_checksum: str
    started_at: datetime
    finished_at: datetime


class WalkForwardRunResponse(WalkForwardRunSummaryResponse):
    created_at: datetime


class WalkForwardPageResponse(ResponseModel):
    runs: list[WalkForwardRunSummaryResponse]
    total: int
    limit: int
    offset: int


class WalkForwardConfigurationResponse(ResponseModel):
    walk_forward: JsonObject
    base_strategy: JsonObject
    config_checksum: str


class WalkForwardActiveETFManifestResponse(ResponseModel):
    etf_id: int
    exchange: str
    symbol: str
    inception_date: date | None
    loaded_price_row_count: int
    first_loaded_price_date: date | None
    last_loaded_price_date: date | None


class WalkForwardInputManifestResponse(ResponseModel):
    version: Literal["wf_provenance_v1"]
    earliest_required_session: date
    configured_end_date: date
    following_session: date | None
    official_sessions: list[date]
    active_etfs: list[WalkForwardActiveETFManifestResponse]
    loaded_price_row_count: int
    first_loaded_price_date: date | None
    last_loaded_price_date: date | None


class WalkForwardInputProvenanceResponse(ResponseModel):
    manifest: WalkForwardInputManifestResponse
    input_data_checksum: str


class WalkForwardOosBenchmarkResponse(ResponseModel):
    key: Literal["equal_weight_monthly", "csi_300_buy_hold"]
    name: str
    total_return: str | None
    annualized_return: str | None
    max_drawdown: str | None
    volatility: str | None
    sharpe_ratio: str | None
    sortino_ratio: str | None
    calmar_ratio: str | None
    longest_drawdown_duration_sessions: int | None
    longest_drawdown_peak_date: date | None
    longest_drawdown_trough_date: date | None
    longest_drawdown_recovery_date: date | None
    total_return_difference: str | None
    annualized_return_difference: str | None
    tracking_error: str | None
    information_ratio: str | None
    capm_alpha: str | None
    capm_beta: str | None
    capm_r_squared: str | None
    capm_observation_count: int | None
    up_capture_ratio: str | None
    up_capture_observation_count: int | None
    down_capture_ratio: str | None
    down_capture_observation_count: int | None


class WalkForwardOosResponse(ResponseModel):
    run_id: int
    strategy_id: str
    config_version: str
    start_date: date
    end_date: date
    status: str
    total_return: str | None
    annualized_return: str | None
    max_drawdown: str | None
    volatility: str | None
    sharpe_ratio: str | None
    sortino_ratio: str | None
    calmar_ratio: str | None
    longest_drawdown_duration_sessions: int | None
    longest_drawdown_peak_date: date | None
    longest_drawdown_trough_date: date | None
    longest_drawdown_recovery_date: date | None
    benchmarks: list[WalkForwardOosBenchmarkResponse]


class WalkForwardWindowResponse(ResponseModel):
    ordinal: int
    train_start: date
    train_end: date
    test_start: date
    test_end: date
    oos_version: str
    selected_parameters: JsonObject
    candidate_count: int
    eligible_count: int
    skipped_count: int
    skip_reason_counts: dict[
        Literal[
            "invalid_config",
            "training_error",
            "training_non_success",
            "missing_train_sharpe",
        ],
        int,
    ]
    train_sharpe: str | None
    oos_backtest: WalkForwardOosResponse


class StitchedOosPointResponse(ResponseModel):
    trade_date: date
    net_value: str
    window_ordinal: int
    is_window_start: bool


class StitchedOosResponse(ResponseModel):
    status: Literal["available", "unavailable_non_contiguous_windows"]
    initial_net_value: str | None
    ending_net_value: str | None
    total_return: str | None
    points: list[StitchedOosPointResponse]


class WalkForwardDetailResponse(ResponseModel):
    run: WalkForwardRunResponse
    configuration: WalkForwardConfigurationResponse
    input_provenance: WalkForwardInputProvenanceResponse
    evidence_version: str
    evidence: WalkForwardEvidenceResponse | WalkForwardEvidenceV2Response
    windows: list[WalkForwardWindowResponse]
    stitched_oos: StitchedOosResponse
