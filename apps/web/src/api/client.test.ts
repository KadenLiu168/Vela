import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiClientError,
  apiRequest,
  bootstrapLocalDatabase,
  fetchFullMarketData,
  fetchIncrementalMarketData,
  generateStrategySignal,
  getBacktestDetail,
  getDashboard,
  getHealth,
  getLatestStrategySignal,
  getStrategySignalDetail,
  listBacktests,
  listStrategySignals,
  runBacktest
} from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiRequest", () => {
  it("returns parsed JSON for successful responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "healthy" }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        })
      )
    );

    await expect(apiRequest<{ status: string }>("/health")).resolves.toEqual({
      status: "healthy"
    });
  });

  it("normalizes HTTP errors with status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "not_found",
              category: "not_found",
              message: "Backtest run not found"
            }
          }),
          {
            headers: { "Content-Type": "application/json" },
            status: 404
          }
        )
      )
    );

    await expect(apiRequest("/missing")).rejects.toMatchObject({
      category: "not_found",
      kind: "http",
      status: 404,
      message: "Backtest run not found"
    });
  });

  it("maps stable validation error envelopes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "validation_error",
              category: "validation",
              message: "Request validation failed"
            }
          }),
          {
            headers: { "Content-Type": "application/json" },
            status: 422
          }
        )
      )
    );

    await expect(apiRequest("/invalid")).rejects.toMatchObject({
      category: "validation",
      kind: "http",
      status: 422,
      message: "Request validation failed"
    });
  });

  it("maps stable operation failed error envelopes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "no_market_data",
              category: "operation_failed",
              message: "No local market prices found"
            }
          }),
          {
            headers: { "Content-Type": "application/json" },
            status: 400
          }
        )
      )
    );

    await expect(apiRequest("/operation")).rejects.toMatchObject({
      category: "operation_failed",
      kind: "http",
      status: 400,
      message: "No local market prices found"
    });
  });

  it("maps stable unexpected error envelopes", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "unexpected_error",
              category: "unexpected",
              message: "Unexpected API error"
            }
          }),
          {
            headers: { "Content-Type": "application/json" },
            status: 500
          }
        )
      )
    );

    await expect(apiRequest("/unexpected")).rejects.toMatchObject({
      category: "unexpected",
      kind: "http",
      status: 500,
      message: "Unexpected API error"
    });
  });

  it("falls back to legacy detail messages with status-derived category", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "legacy not found" }), {
          headers: { "Content-Type": "application/json" },
          status: 404
        })
      )
    );

    await expect(apiRequest("/missing")).rejects.toMatchObject({
      category: "not_found",
      kind: "http",
      status: 404,
      message: "legacy not found"
    });
  });

  it("normalizes network errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));

    await expect(apiRequest("/health")).rejects.toMatchObject({
      category: "network",
      kind: "network",
      message: "Network request failed"
    });
  });
});

it("calls health through the shared client", async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ status: "healthy" }), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(getHealth()).resolves.toEqual({ status: "healthy" });
  expect(fetchMock).toHaveBeenCalledWith("/api/health", undefined);
});

it("calls dashboard through the shared client", async () => {
  const dashboard = {
    strategy: {
      strategy_id: "dual_momentum",
      version: "v1",
      universe_config: "config/etf_universe.yaml",
      momentum: {
        short_window_days: 20,
        long_window_days: 60
      },
      score_weights: { short: 0.4, long: 0.6 },
      trend_filter: { enabled: true },
      selection: { top_n: 2 },
      defense: {
        assets: [
          {
            exchange: "NASDAQ",
            symbol: "BIL"
          }
        ]
      },
      costs: { transaction_cost_bps: 5 },
      performance: { risk_free_rate: 0.02 },
      rebalance: { frequency: "weekly" }
    },
    market_data: {
      price_rows: 1200,
      covered_etfs: 8,
      earliest_trade_date: "2025-01-02",
      latest_trade_date: "2026-06-23",
      etf_list: [
        { exchange: "NYSEARCA", symbol: "SPY", name: "SPY ETF", category: "equity_us" },
        { exchange: "NYSEARCA", symbol: "QQQ", name: "QQQ ETF", category: "equity_us_tech" },
      ],
    },
    latest_signal: {
      signal_id: 42,
      signal_date: "2026-06-23",
      config_version: "v1",
      status: "success",
      result: "rebalance",
      generated_at: "2026-06-23T09:30:00",
      is_fallback: false,
      position_count: 2
    },
    recent_backtest: {
      run_id: 7,
      strategy_id: "dual_momentum",
      config_version: "v1",
      start_date: "2026-01-01",
      end_date: "2026-06-01",
      status: "success",
      total_return: "0.120000",
      max_drawdown: "-0.050000",
      sharpe_ratio: "1.100000",
      started_at: "2026-06-02T09:00:00"
    },
    recent_fetch_logs: [
      {
        fetch_log_id: 11,
        fetch_time: "2026-06-24T08:00:00",
        mode: "incremental",
        status: "partial",
        rows_fetched: 25,
        rows_inserted: 20,
        rows_updated: 5,
        error_summary: "QQQ: provider timeout"
      }
    ]
  };
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(dashboard), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(getDashboard()).resolves.toEqual(dashboard);
  expect(fetchMock).toHaveBeenCalledWith("/api/dashboard", undefined);
});

it("calls incremental market data fetch through the shared client", async () => {
  const fetchResult = {
    status: "success",
    requested_etf_count: 1,
    rows_fetched: 1,
    rows_inserted: 1,
    rows_updated: 0,
    failed_symbols: [],
    error_message: null
  };
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(fetchResult), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(fetchIncrementalMarketData()).resolves.toEqual(fetchResult);
  expect(fetchMock).toHaveBeenCalledWith("/api/market-data/fetch?mode=incremental", {
    method: "POST"
  });
});

it("calls full market data fetch through the shared client", async () => {
  const fetchResult = {
    status: "success",
    requested_etf_count: 1,
    rows_fetched: 1,
    rows_inserted: 1,
    rows_updated: 0,
    failed_symbols: [],
    error_message: null
  };
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(fetchResult), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(fetchFullMarketData()).resolves.toEqual(fetchResult);
  expect(fetchMock).toHaveBeenCalledWith("/api/market-data/fetch?mode=full", {
    method: "POST"
  });
});

it("calls bootstrap local database through the shared client", async () => {
  const bootstrapResult = {
    status: "success",
    failed_step: null,
    total_duration_seconds: 0.5,
    steps: [
      { name: "migrate", status: "success", duration_seconds: 0.1, error_message: null },
      { name: "sync_etf_pool", status: "success", duration_seconds: 0.2, error_message: null },
      { name: "fetch_full_market_data", status: "success", duration_seconds: 0.2, error_message: null }
    ]
  };
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(bootstrapResult), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(bootstrapLocalDatabase()).resolves.toEqual(bootstrapResult);
  expect(fetchMock).toHaveBeenCalledWith("/api/setup/bootstrap", {
    method: "POST"
  });
});

it("calls strategy signal generation through the shared client", async () => {
  const generateResult = {
    signal_id: 42,
    signal_date: "2026-06-23",
    config_version: "v1",
    status: "success",
    result: "rebalance",
    error_message: null,
    source: "manual",
    positions: [
      {
        etf_id: 1,
        exchange: "SSE",
        symbol: "510300",
        target_weight: "0.500000",
        rank: 1,
        score: "0.800000"
      }
    ]
  };
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(generateResult), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(generateStrategySignal()).resolves.toEqual(generateResult);
  expect(fetchMock).toHaveBeenCalledWith("/api/strategy-signals/generate", {
    method: "POST"
  });
});

it("encodes an explicit scheduled strategy signal source", async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ source: "scheduled" }), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await generateStrategySignal("scheduled");

  expect(fetchMock).toHaveBeenCalledWith("/api/strategy-signals/generate?source=scheduled", {
    method: "POST"
  });
});

it("calls latest strategy signal through the shared client", async () => {
  const latestSignal = {
    has_signal: true,
    signal: {
      signal_id: 42,
      signal_date: "2026-06-23",
      config_version: "v1",
      result: "rebalance",
      generated_at: "2026-06-23T09:30:00",
      is_fallback: false
    },
    positions: [
      {
        exchange: "SSE",
        symbol: "510300",
        name: "沪深300ETF",
        target_weight: "0.500000",
        rank: 1,
        score: "0.800000",
        is_fallback: false
      }
    ]
  };
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(latestSignal), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(getLatestStrategySignal()).resolves.toEqual(latestSignal);
  expect(fetchMock).toHaveBeenCalledWith("/api/strategy-signals/latest", undefined);
});

it("calls run backtest through the shared client", async () => {
  const backtestResult = {
    run_id: 8,
    status: "success",
    start_date: "2026-01-01",
    end_date: "2026-01-31",
    trading_day_count: 21,
    signal_count: 5,
    total_return: "0.120000",
    annualized_return: "1.440000",
    max_drawdown: "-0.050000",
    volatility: "0.200000",
    sharpe_ratio: "1.100000"
  };
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(backtestResult), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(runBacktest("2026-01-01", "2026-01-31")).resolves.toEqual(backtestResult);
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/backtests/run?startDate=2026-01-01&endDate=2026-01-31",
    {
      method: "POST"
    }
  );
});

it("calls backtest detail through the shared client", async () => {
  const detail = {
    run: {
      run_id: 8,
      strategy_id: "dual_momentum",
      config_version: "v1",
      start_date: "2026-01-01",
      end_date: "2026-01-31",
      parameters_json: "{\"top_n\": 2}",
      status: "success",
      error_message: null,
      started_at: "2026-02-01T09:00:00",
      finished_at: "2026-02-01T09:05:00"
    },
    metrics: {
      total_return: "0.120000",
      annualized_return: "1.440000",
      max_drawdown: "-0.050000",
      volatility: "0.200000",
      sharpe_ratio: "1.100000"
    },
    equity_curve: [
      {
        trade_date: "2026-01-02",
        net_value: "1.010000",
        cash: "100.000000",
        market_value: "9900.000000",
        total_assets: "10000.000000",
        positions_json: "[{\"symbol\": \"510300\", \"weight\": 1.0}]"
      }
    ]
  };
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(detail), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(getBacktestDetail("8")).resolves.toEqual(detail);
  expect(fetchMock).toHaveBeenCalledWith("/api/backtests/8", undefined);
});

it("calls strategy signal list through the shared client", async () => {
  const list = {
    signals: [
      {
        signal_id: 42,
        signal_date: "2026-06-23",
        config_version: "v1",
        result: "rebalance",
        generated_at: "2026-06-23T09:30:00",
        is_fallback: false,
        position_count: 2
      }
    ]
  };
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(list), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(listStrategySignals(20, 0)).resolves.toEqual(list);
  expect(fetchMock).toHaveBeenCalledWith("/api/strategy-signals?limit=20&offset=0", undefined);
});

it("calls strategy signal detail through the shared client", async () => {
  const detail = {
    signal: {
      signal_id: 42,
      signal_date: "2026-06-23",
      strategy_id: "dual_momentum",
      config_version: "v1",
      generated_at: "2026-06-23T09:30:00",
      result: "rebalance",
      is_fallback: false
    },
    positions: [
      {
        exchange: "SSE",
        symbol: "510300",
        name: "沪深300ETF",
        target_weight: "0.333333",
        rank: 1,
        score: "0.812345",
        is_fallback: false
      }
    ]
  };
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(detail), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(getStrategySignalDetail("42")).resolves.toEqual(detail);
  expect(fetchMock).toHaveBeenCalledWith("/api/strategy-signals/42", undefined);
});

it("calls backtest list with limit and offset through the shared client", async () => {
  const list = {
    runs: [
      {
        run_id: 8,
        strategy_id: "dual_momentum",
        config_version: "v1",
        start_date: "2026-01-01",
        end_date: "2026-01-31",
        status: "success",
        started_at: "2026-02-01T09:00:00",
        finished_at: "2026-02-01T09:05:00",
        total_return: "0.120000",
        annualized_return: "1.440000",
        max_drawdown: "-0.050000",
        volatility: "0.200000",
        sharpe_ratio: "1.100000"
      }
    ]
  };
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(list), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(listBacktests(10, 10)).resolves.toEqual(list);
  expect(fetchMock).toHaveBeenCalledWith("/api/backtests?limit=10&offset=10", undefined);
});

it("exposes a typed API client error", () => {
  const error = new ApiClientError("HTTP request failed", {
    category: "unexpected",
    kind: "http",
    status: 500
  });

  expect(error).toMatchObject({
    category: "unexpected",
    kind: "http",
    status: 500,
    message: "HTTP request failed"
  });
});
