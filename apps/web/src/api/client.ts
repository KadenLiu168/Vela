const DEFAULT_API_BASE_URL = "/api";

type ApiClientErrorOptions =
  | {
      kind: "http";
      status: number;
    }
  | {
      kind: "network";
      status?: never;
    };

export class ApiClientError extends Error {
  kind: ApiClientErrorOptions["kind"];
  status?: number;

  constructor(message: string, options: ApiClientErrorOptions) {
    super(message);
    this.name = "ApiClientError";
    this.kind = options.kind;
    this.status = options.kind === "http" ? options.status : undefined;
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
    asset: {
      exchange: string;
      symbol: string;
    };
  };
  costs: {
    transaction_cost_bps: number;
  };
  performance: Record<string, unknown>;
};

export type DashboardMarketDataStatus = {
  price_rows: number;
  covered_etfs: number;
  earliest_trade_date: string | null;
  latest_trade_date: string | null;
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
  strategy_name: string;
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
    throw new ApiClientError(await getErrorMessage(response), {
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

export function getLatestStrategySignal(): Promise<LatestStrategySignalResponse> {
  return apiRequest<LatestStrategySignalResponse>("/strategy-signals/latest");
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();

    if (isObjectWithStringDetail(body)) {
      return body.detail;
    }
  } catch {
    return response.statusText || "HTTP request failed";
  }

  return response.statusText || "HTTP request failed";
}

function isObjectWithStringDetail(value: unknown): value is { detail: string } {
  return (
    typeof value === "object" &&
    value !== null &&
    "detail" in value &&
    typeof value.detail === "string"
  );
}
