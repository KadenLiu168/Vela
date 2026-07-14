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
    };

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

export type DashboardStrategySummary = {
  strategy_id: string;
  version: string;
  universe_config: string;
  momentum: {
    short_window_days: number;
    long_window_days: number;
  };
  score_weights: {
    short: number;
    long: number;
  };
  trend_filter: Record<string, unknown>;
  selection: {
    top_n: number;
  };
  defense: {
    assets: {
      exchange: string;
      symbol: string;
    }[];
  };
  costs: {
    transaction_cost_bps: number;
  };
  performance: Record<string, unknown>;
  rebalance: {
    frequency: string;
  };
};

export type EtfBrief = {
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
};

export type BacktestDetailResponse = {
  run: BacktestDetailRun;
  metrics: BacktestDetailMetrics;
  equity_curve: BacktestEquityCurvePoint[];
};

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
};

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
};

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
};

export type StrategySignalDetailPosition = {
  exchange: string;
  symbol: string;
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

export function generateStrategySignal(): Promise<StrategySignalGenerationResponse> {
  return apiRequest<StrategySignalGenerationResponse>("/strategy-signals/generate", {
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

export function getLatestStrategySignal(): Promise<LatestStrategySignalResponse> {
  return apiRequest<LatestStrategySignalResponse>("/strategy-signals/latest");
}

export function listStrategySignals(limit = 20, offset = 0): Promise<StrategySignalListResponse> {
  const searchParams = new URLSearchParams({
    limit: String(limit),
    offset: String(offset)
  });

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
