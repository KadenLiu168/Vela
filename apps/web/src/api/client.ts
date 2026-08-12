const DEFAULT_API_BASE_URL = "/api";

export type ApiErrorCategory = "validation" | "not_found" | "operation_failed" | "unexpected" | "network";

type ApiClientErrorOptions =
  | {
      kind: "http";
      status: number;
      category: ApiErrorCategory;
    }
  | {
      kind: "network";
      status?: never;
      category?: never;
    }

export class ApiClientError extends Error {
  kind: ApiClientErrorOptions["kind"];
  status?: number;
  category: ApiErrorCategory;

  constructor(message: string, options: ApiClientErrorOptions) {
    super(message);
    this.name = "ApiClientError";
    this.kind = options.kind;
    this.status = options.kind === "http" ? options.status : undefined;
    this.category = options.kind === "http" ? options.category : "network";
  }
}

export type HealthResponse = {
  status: string;
};

export type DashboardResponse = {
  strategy: DashboardStrategySummary;
  market_data: DashboardMarketDataStatus;
  latest_signal: DashboardSignalSummary | null;
  recent_backtest: DashboardBacktestSummary | null;
  recent_fetch_logs: DashboardFetchLogSummary[];
};

type DashboardStrategyCommon = {
  strategy_id: string;
  version: string;
  universe_config: string;
  costs: { transaction_cost_bps: number };
  performance: Record<string, unknown>;
  rebalance: { frequency: string };
};

export type DashboardStrategySummary = DashboardStrategyCommon & (
  | {
      type: "dual_momentum";
      parameters: {
        momentum: {
          short_window_days: number;
          long_window_days: number;
        };
        score_weights: {
          short: number;
          long: number;
        };
        trend_filter: {
          moving_average_days: 60 | 120 | 250;
          price_relation: "above" | "below";
        };
        selection: {
          top_n: number;
        };
        defense: {
          assets: {
            exchange: string;
            symbol: string;
          }[];
        };
      };
    }
  | { type: "equal_weight"; parameters: Record<string, never> }
);

export type EtfBrief = {
  etf_id: number;
  exchange: string;
  symbol: string;
  name: string;
  category: string | null;
  earliest_trade_date: string | null;
};

export type DashboardMarketDataStatus = {
  price_rows: number;
  covered_etfs: number;
  earliest_trade_date: string | null;
  latest_trade_date: string | null;
  etf_list: EtfBrief[];
};

export type DashboardSignalSummary = {
  signal_id: number;
  signal_date: string;
  config_version: string;
  status: string;
  result: string | null;
  generated_at: string;
  is_fallback: boolean;
  position_count: number;
};

export type DashboardBacktestSummary = {
  run_id: number;
  strategy_id: string;
  config_version: string;
  start_date: string;
  end_date: string;
  status: string;
  total_return: string | null;
  max_drawdown: string | null;
  sharpe_ratio: string | null;
  started_at: string;
};

export type DashboardFetchLogSummary = {
  fetch_log_id: number;
  fetch_time: string;
  mode: string;
  status: string;
  rows_fetched: number | null;
  rows_inserted: number | null;
  rows_updated: number | null;
  error_summary: string | null;
};

export type MarketDataFetchResponse = {
  status: string;
  requested_etf_count: number;
  rows_fetched: number;
  rows_inserted: number;
  rows_updated: number;
  failed_symbols: string[];
  error_message: string | null;
};

export type StrategySignalGenerationResponse = {
  signal_id: number;
  signal_date: string;
  config_version: string;
  status: string;
  result: string | null;
  error_message: string | null;
  source: StrategySignalSource;
  positions: StrategySignalGenerationPosition[];
};

export type BacktestRunResponse = {
  run_id: number;
  status: string;
  start_date: string;
  end_date: string;
  trading_day_count: number;
  signal_count: number;
  total_return: string | null;
  annualized_return: string | null;
  max_drawdown: string | null;
  volatility: string | null;
  sharpe_ratio: string | null;
  sortino_ratio: string | null;
  calmar_ratio: string | null;
  longest_drawdown_duration_sessions: number | null;
  longest_drawdown_peak_date: string | null;
  longest_drawdown_trough_date: string | null;
  longest_drawdown_recovery_date: string | null;
  benchmarks: BacktestBenchmark[];
};

export type ReturnStabilityRollingPoint = {
  window_start_date: string;
  trade_date: string;
  total_return: string;
  volatility: string;
  sharpe_ratio: string | null;
};

export type ReturnStabilityCalendarBucket = {
  period: string;
  first_date: string;
  last_date: string;
  observation_count: number;
  total_return: string;
  is_partial: boolean;
};

export type ReturnStabilityEntity = {
  window_sessions: number;
  rolling_status: "available" | "insufficient_observations";
  sharpe_status:
    | "available"
    | "insufficient_observations"
    | "unavailable_missing_risk_free_rate";
  source_point_count: number;
  effective_return_count: number;
  rolling: ReturnStabilityRollingPoint[];
  monthly: ReturnStabilityCalendarBucket[];
  yearly: ReturnStabilityCalendarBucket[];
};

export type ReturnStabilityBenchmark = ReturnStabilityEntity & {
  key: string;
  name: string;
};

export type ReturnStability = {
  strategy: ReturnStabilityEntity;
  benchmarks: ReturnStabilityBenchmark[];
};

export type DistributionEvidenceStatus =
  | "sufficient"
  | "insufficient_evidence"
  | "unavailable_legacy";

export type TailDistributionFields = {
  historical_var_95: string | null;
  historical_cvar_95: string | null;
  return_skewness: string | null;
  return_excess_kurtosis: string | null;
  distribution_observation_count: number | null;
  tail_observation_count: number | null;
  distribution_evidence_status: DistributionEvidenceStatus;
};

export type BacktestDetailResponse = {
  run: BacktestDetailRun;
  metrics: BacktestDetailMetrics;
  equity_curve: BacktestEquityCurvePoint[];
  signal_ids: number[];
  signal_count: number;
  benchmarks: BacktestBenchmark[];
  return_stability: ReturnStability;
};

export type BacktestBenchmark = {
  key: string;
  name: string;
  total_return: string | null;
  annualized_return: string | null;
  max_drawdown: string | null;
  volatility: string | null;
  sharpe_ratio: string | null;
  sortino_ratio: string | null;
  calmar_ratio: string | null;
  longest_drawdown_duration_sessions: number | null;
  longest_drawdown_peak_date: string | null;
  longest_drawdown_trough_date: string | null;
  longest_drawdown_recovery_date: string | null;
  total_return_difference: string | null;
  annualized_return_difference: string | null;
  tracking_error: string | null;
  information_ratio: string | null;
  capm_alpha: string | null;
  capm_beta: string | null;
  capm_r_squared: string | null;
  capm_observation_count: number | null;
  up_capture_ratio: string | null;
  up_capture_observation_count: number | null;
  down_capture_ratio: string | null;
  down_capture_observation_count: number | null;
  equity_curve: Array<{ trade_date: string; net_value: string }>;
} & TailDistributionFields;

export type BacktestDetailRun = {
  run_id: number;
  strategy_id: string;
  config_version: string;
  start_date: string;
  end_date: string;
  parameters_json: string | null;
  status: string;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
};

export type BacktestDetailMetrics = {
  total_return: string | null;
  annualized_return: string | null;
  max_drawdown: string | null;
  volatility: string | null;
  sharpe_ratio: string | null;
  sortino_ratio: string | null;
  calmar_ratio: string | null;
  longest_drawdown_duration_sessions: number | null;
  longest_drawdown_peak_date: string | null;
  longest_drawdown_trough_date: string | null;
  longest_drawdown_recovery_date: string | null;
} & TailDistributionFields;

export type BacktestEquityCurvePoint = {
  trade_date: string;
  net_value: string | null;
  cash: string | null;
  market_value: string | null;
  total_assets: string | null;
  positions_json: string | null;
};

export type BootstrapResponse = {
  status: string;
  failed_step: string | null;
  total_duration_seconds: number;
  steps: BootstrapStepResult[];
};

export type BootstrapStepResult = {
  name: string;
  status: string;
  duration_seconds: number;
  error_message: string | null;
};

export type StrategySignalGenerationPosition = {
  etf_id: number;
  exchange: string;
  symbol: string;
  target_weight: string;
  rank: number | null;
  score: string | null;
};

export type LatestStrategySignalResponse = {
  has_signal: boolean;
  signal: LatestStrategySignal | null;
  positions: LatestStrategySignalPosition[];
};

export type LatestStrategySignal = {
  signal_id: number;
  signal_date: string;
  config_version: string;
  result: string | null;
  generated_at: string;
  is_fallback: boolean;
};

export type LatestStrategySignalPosition = {
  exchange: string;
  symbol: string;
  name: string;
  target_weight: string;
  rank: number | null;
  score: string | null;
  is_fallback: boolean;
};

export type BacktestListItem = {
  run_id: number;
  strategy_id: string;
  config_version: string;
  start_date: string;
  end_date: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  total_return: string | null;
  annualized_return: string | null;
  max_drawdown: string | null;
  volatility: string | null;
  sharpe_ratio: string | null;
};

export type BacktestListResponse = {
  runs: BacktestListItem[];
};

export type StrategySignalListItem = {
  signal_id: number;
  signal_date: string;
  config_version: string;
  result: string | null;
  generated_at: string;
  is_fallback: boolean;
  position_count: number;
  source: StrategySignalSource;
  backtest_run_id: number | null;
};

export type StrategySignalSource = "manual" | "scheduled" | "backtest" | "legacy";
export type LiveStrategySignalSource = "manual" | "scheduled";

export type StrategySignalListResponse = {
  signals: StrategySignalListItem[];
};

export type StrategySignalDetailMetadata = {
  signal_id: number;
  signal_date: string;
  strategy_id: string;
  config_version: string;
  generated_at: string;
  result: string | null;
  is_fallback: boolean;
  source: StrategySignalSource;
  backtest_run_id: number | null;
};

export type StrategySignalDetailPosition = {
  exchange: string;
  symbol: string;
  name: string;
  target_weight: string;
  rank: number | null;
  score: string | null;
  is_fallback: boolean;
};

export type StrategySignalDetailResponse = {
  signal: StrategySignalDetailMetadata;
  positions: StrategySignalDetailPosition[];
};

export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
  baseUrl = getApiBaseUrl()
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${baseUrl}${path}`, init);
  } catch {
    throw new ApiClientError("Network request failed", { kind: "network" });
  }

  if (!response.ok) {
    const apiError = await getApiError(response);
    throw new ApiClientError(apiError.message, {
      category: apiError.category,
      kind: "http",
      status: response.status
    });
  }

  return response.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health");
}

export function getDashboard(): Promise<DashboardResponse> {
  return apiRequest<DashboardResponse>("/dashboard");
}

export type PriceTrendRange = "1m" | "3m" | "1y" | "3y" | "max";

export type EtfPriceTrendPoint = {
  trade_date: string;
  price: string;
};

export type EtfPriceTrendResponse = {
  etf: {
    id: number;
    exchange: string;
    symbol: string;
    name: string;
  };
  points: EtfPriceTrendPoint[];
};

export function getEtfPriceTrend(
  etfId: string,
  range: PriceTrendRange
): Promise<EtfPriceTrendResponse> {
  return apiRequest<EtfPriceTrendResponse>(
    `/etfs/${encodeURIComponent(etfId)}/prices?range=${range}`
  );
}

export function fetchIncrementalMarketData(): Promise<MarketDataFetchResponse> {
  return apiRequest<MarketDataFetchResponse>("/market-data/fetch?mode=incremental", {
    method: "POST"
  });
}

export function fetchFullMarketData(): Promise<MarketDataFetchResponse> {
  return apiRequest<MarketDataFetchResponse>("/market-data/fetch?mode=full", {
    method: "POST"
  });
}

export function bootstrapLocalDatabase(): Promise<BootstrapResponse> {
  return apiRequest<BootstrapResponse>("/setup/bootstrap", {
    method: "POST"
  });
}

export function generateStrategySignal(
  source?: LiveStrategySignalSource
): Promise<StrategySignalGenerationResponse> {
  const suffix = source === undefined ? "" : `?source=${encodeURIComponent(source)}`;
  return apiRequest<StrategySignalGenerationResponse>(`/strategy-signals/generate${suffix}`, {
    method: "POST"
  });
}

export function runBacktest(startDate: string, endDate: string): Promise<BacktestRunResponse> {
  const searchParams = new URLSearchParams({
    startDate,
    endDate
  });

  return apiRequest<BacktestRunResponse>(`/backtests/run?${searchParams.toString()}`, {
    method: "POST"
  });
}

export function getBacktestDetail(runId: string): Promise<BacktestDetailResponse> {
  return apiRequest<BacktestDetailResponse>(`/backtests/${encodeURIComponent(runId)}`);
}

export type BacktestSignalSummary = {
  signal_id: number;
  signal_date: string;
  result: string | null;
  backtest_run_id: number;
};

export type BacktestSignalsResponse = {
  signals: BacktestSignalSummary[];
};

export type WalkForwardJsonValue =
  | null
  | boolean
  | number
  | string
  | WalkForwardJsonValue[]
  | { [key: string]: WalkForwardJsonValue };

export type WalkForwardEvidenceStatus = "sufficient" | "insufficient_evidence";
export type WalkForwardBenchmarkKey = "equal_weight_monthly" | "csi_300_buy_hold";
export type WalkForwardSkipReason =
  | "invalid_config"
  | "training_error"
  | "training_non_success"
  | "missing_train_sharpe";

export type WalkForwardMetricSummary = {
  mean: number | null;
  median: number | null;
  min: number | null;
  max: number | null;
  std: number | null;
  window_count: number;
  valid_count: number;
  evidence_status: WalkForwardEvidenceStatus;
};

export type WalkForwardRateSummary = {
  numerator: number;
  denominator: number;
  value: number | null;
  window_count: number;
  valid_count: number;
  evidence_status: WalkForwardEvidenceStatus;
};

export type WalkForwardBenchmarkEvidence = {
  total_return_difference: WalkForwardMetricSummary;
  annualized_return_difference: WalkForwardMetricSummary;
  tracking_error: WalkForwardMetricSummary;
  information_ratio: WalkForwardMetricSummary;
  outperformance_rate: WalkForwardRateSummary;
  capm_alpha?: WalkForwardMetricSummary;
  capm_beta?: WalkForwardMetricSummary;
  capm_r_squared?: WalkForwardMetricSummary;
  up_capture_ratio?: WalkForwardMetricSummary;
  down_capture_ratio?: WalkForwardMetricSummary;
};

export type WalkForwardTailDistributionOwner = {
  historical_var_95: number | null;
  historical_cvar_95: number | null;
  return_skewness: number | null;
  return_excess_kurtosis: number | null;
  observation_count: number;
  tail_observation_count: number;
  evidence_status: WalkForwardEvidenceStatus;
};

export type WalkForwardTailDistributionWindow = {
  ordinal: number;
  owners: Record<string, WalkForwardTailDistributionOwner>;
};

export type WalkForwardTailDistributionAggregates = {
  historical_var_95: WalkForwardMetricSummary;
  historical_cvar_95: WalkForwardMetricSummary;
  return_skewness: WalkForwardMetricSummary;
  return_excess_kurtosis: WalkForwardMetricSummary;
};

export type WalkForwardTailDistribution = {
  per_window: WalkForwardTailDistributionWindow[];
  aggregates: Record<string, WalkForwardTailDistributionAggregates>;
};

export type WalkForwardEvidence = {
  metrics: {
    total_return: WalkForwardMetricSummary;
    annualized_return: WalkForwardMetricSummary;
    sharpe_ratio: WalkForwardMetricSummary;
    max_drawdown: WalkForwardMetricSummary;
    volatility: WalkForwardMetricSummary;
    sortino_ratio: WalkForwardMetricSummary;
    calmar_ratio: WalkForwardMetricSummary;
    longest_drawdown_duration_sessions: WalkForwardMetricSummary;
  };
  positive_window_rate: WalkForwardRateSummary;
  generalization_gap: WalkForwardMetricSummary;
  benchmarks: Record<WalkForwardBenchmarkKey, WalkForwardBenchmarkEvidence>;
  parameter_stability: Record<
    string,
    {
      value_frequencies: Record<string, number>;
      transition_count: number;
      comparison_count: number;
      transition_rate: number | null;
    }
  >;
  tail_distribution?: WalkForwardTailDistribution;
};

export type WalkForwardRunStatus = "queued" | "running" | "success" | "failed";

export type WalkForwardRunSummary = {
  run_id: number;
  strategy_id: string;
  start_date: string;
  end_date: string;
  window_count: number;
  provenance_version: string;
  evidence_version: string;
  config_checksum: string;
  input_data_checksum: string;
  status: WalkForwardRunStatus;
  error_message: string | null;
  attempt_count: number;
  claimed_at: string | null;
  heartbeat_at: string | null;
  lease_expires_at: string | null;
  started_at: string;
  finished_at: string | null;
};

export type WalkForwardRunAcceptedResponse = {
  walk_forward_run_id: number;
  status: "queued";
};

export type WalkForwardPageResponse = {
  runs: WalkForwardRunSummary[];
  total: number;
  limit: number;
  offset: number;
};

export type WalkForwardInputManifestV1 = {
  version: "wf_provenance_v1";
  earliest_required_session: string;
  configured_end_date: string;
  following_session: string | null;
  official_sessions: string[];
  active_etfs: Array<{
    etf_id: number;
    exchange: string;
    symbol: string;
    inception_date: string | null;
    loaded_price_row_count: number;
    first_loaded_price_date: string | null;
    last_loaded_price_date: string | null;
  }>;
  loaded_price_row_count: number;
  first_loaded_price_date: string | null;
  last_loaded_price_date: string | null;
};

export type WalkForwardInputManifestV2 = {
  version: "wf_provenance_v2";
  resolution_policy_version: string;
  earliest_required_session: string;
  configured_end_date: string;
  following_session: string | null;
  official_sessions: string[];
  active_etfs: Array<{
    etf_id: number;
    exchange: string;
    symbol: string;
    inception_date: string | null;
    listing_date: string;
    raw_price_row_count: number;
    first_raw_price_date: string | null;
    last_raw_price_date: string | null;
    derived_session_count: number;
    first_derived_session_date: string | null;
    last_derived_session_date: string | null;
    status_evidence: Array<{
      trade_date: string;
      status: "full_day_suspension" | "corporate_action_halt";
      reason: string;
      source_uri: string;
      source_published_date: string;
      share_ratio: string | null;
      resolution: "confirmed_non_trading_carry";
      carried_adjusted_value: string;
      carry_from_trade_date: string;
    }>;
  }>;
  raw_price_row_count: number;
  first_raw_price_date: string | null;
  last_raw_price_date: string | null;
  derived_session_count: number;
  first_derived_session_date: string | null;
  last_derived_session_date: string | null;
};

export type WalkForwardInputManifest = WalkForwardInputManifestV1 | WalkForwardInputManifestV2;

export type WalkForwardBenchmark = {
  key: WalkForwardBenchmarkKey;
  name: string;
  total_return: string | null;
  annualized_return: string | null;
  max_drawdown: string | null;
  volatility: string | null;
  sharpe_ratio: string | null;
  sortino_ratio: string | null;
  calmar_ratio: string | null;
  longest_drawdown_duration_sessions: number | null;
  longest_drawdown_peak_date: string | null;
  longest_drawdown_trough_date: string | null;
  longest_drawdown_recovery_date: string | null;
  total_return_difference: string | null;
  annualized_return_difference: string | null;
  tracking_error: string | null;
  information_ratio: string | null;
  capm_alpha: string | null;
  capm_beta: string | null;
  capm_r_squared: string | null;
  capm_observation_count: number | null;
  up_capture_ratio: string | null;
  up_capture_observation_count: number | null;
  down_capture_ratio: string | null;
  down_capture_observation_count: number | null;
};

export type WalkForwardOosBacktest = {
  run_id: number;
  strategy_id: string;
  config_version: string;
  start_date: string;
  end_date: string;
  status: string;
  total_return: string | null;
  annualized_return: string | null;
  max_drawdown: string | null;
  volatility: string | null;
  sharpe_ratio: string | null;
  sortino_ratio: string | null;
  calmar_ratio: string | null;
  longest_drawdown_duration_sessions: number | null;
  longest_drawdown_peak_date: string | null;
  longest_drawdown_trough_date: string | null;
  longest_drawdown_recovery_date: string | null;
  benchmarks: WalkForwardBenchmark[];
};

export type WalkForwardDetailResponse = {
  run: WalkForwardRunSummary & { created_at: string };
  configuration: {
    walk_forward: { [key: string]: WalkForwardJsonValue };
    base_strategy: { [key: string]: WalkForwardJsonValue };
    config_checksum: string;
  };
  input_provenance: {
    manifest: WalkForwardInputManifest;
    input_data_checksum: string;
  };
  evidence_version: string;
  evidence: WalkForwardEvidence | null;
  stitched_oos: {
    status: "available" | "unavailable_non_contiguous_windows";
    initial_net_value: string | null;
    ending_net_value: string | null;
    total_return: string | null;
    points: Array<{
      trade_date: string;
      net_value: string;
      window_ordinal: number;
      is_window_start: boolean;
    }>;
  } | null;
  windows: Array<{
    ordinal: number;
    train_start: string;
    train_end: string;
    test_start: string;
    test_end: string;
    oos_version: string;
    selected_parameters: { [key: string]: WalkForwardJsonValue };
    candidate_count: number;
    eligible_count: number;
    skipped_count: number;
    skip_reason_counts: Partial<Record<WalkForwardSkipReason, number>>;
    train_sharpe: string | null;
    oos_backtest: WalkForwardOosBacktest;
  }>;
};

export function listBacktestSignals(
  runId: string,
  limit = 20,
  offset = 0
): Promise<BacktestSignalsResponse> {
  const searchParams = new URLSearchParams({
    limit: String(limit),
    offset: String(offset)
  });

  return apiRequest<BacktestSignalsResponse>(
    `/backtests/${encodeURIComponent(runId)}/signals?${searchParams.toString()}`
  );
}

export function listWalkForwards(limit = 10, offset = 0): Promise<WalkForwardPageResponse> {
  const searchParams = new URLSearchParams({
    limit: String(limit),
    offset: String(offset)
  });
  return apiRequest<WalkForwardPageResponse>(`/walk-forwards?${searchParams.toString()}`);
}

export function runWalkForward(): Promise<WalkForwardRunAcceptedResponse> {
  return apiRequest<WalkForwardRunAcceptedResponse>("/walk-forwards/run", {
    method: "POST"
  });
}

export function getWalkForwardDetail(runId: string): Promise<WalkForwardDetailResponse> {
  return apiRequest<WalkForwardDetailResponse>(`/walk-forwards/${encodeURIComponent(runId)}`);
}

export function getLatestStrategySignal(): Promise<LatestStrategySignalResponse> {
  return apiRequest<LatestStrategySignalResponse>("/strategy-signals/latest");
}

export function listStrategySignals(
  limit = 20,
  offset = 0,
  source?: StrategySignalSource
): Promise<StrategySignalListResponse> {
  const searchParams = new URLSearchParams({
    limit: String(limit),
    offset: String(offset)
  });
  if (source !== undefined) {
    searchParams.set("source", source);
  }

  return apiRequest<StrategySignalListResponse>(`/strategy-signals?${searchParams.toString()}`);
}

export function getStrategySignalDetail(signalId: string): Promise<StrategySignalDetailResponse> {
  return apiRequest<StrategySignalDetailResponse>(
    `/strategy-signals/${encodeURIComponent(signalId)}`
  );
}

export function listBacktests(limit = 10, offset = 0): Promise<BacktestListResponse> {
  const searchParams = new URLSearchParams({
    limit: String(limit),
    offset: String(offset)
  });

  return apiRequest<BacktestListResponse>(`/backtests?${searchParams.toString()}`);
}

async function getApiError(response: Response): Promise<{ category: ApiErrorCategory; message: string }> {
  try {
    const body: unknown = await response.json();

    if (isStableApiError(body)) {
      return {
        category: body.error.category,
        message: body.error.message
      };
    }

    if (isObjectWithStringDetail(body)) {
      return {
        category: getFallbackCategory(response.status),
        message: body.detail
      };
    }
  } catch {
    return {
      category: getFallbackCategory(response.status),
      message: response.statusText || "HTTP request failed"
    };
  }

  return {
    category: getFallbackCategory(response.status),
    message: response.statusText || "HTTP request failed"
  };
}

function isObjectWithStringDetail(value: unknown): value is { detail: string } {
  return (
    typeof value === "object" &&
    value !== null &&
    "detail" in value &&
    typeof value.detail === "string"
  );
}

function isStableApiError(value: unknown): value is {
  error: { category: ApiErrorCategory; message: string };
} {
  if (
    typeof value !== "object" ||
    value === null ||
    !("error" in value) ||
    typeof value.error !== "object" ||
    value.error === null
  ) {
    return false;
  }

  const error = value.error as Record<string, unknown>;
  return isApiErrorCategory(error.category) && typeof error.message === "string";
}

function isApiErrorCategory(value: unknown): value is ApiErrorCategory {
  return (
    value === "validation" ||
    value === "not_found" ||
    value === "operation_failed" ||
    value === "unexpected"
  );
}

function getFallbackCategory(status: number): ApiErrorCategory {
  if (status === 422) {
    return "validation";
  }

  if (status === 404) {
    return "not_found";
  }

  if (status >= 500) {
    return "unexpected";
  }

  return "operation_failed";
}
