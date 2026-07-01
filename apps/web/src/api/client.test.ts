import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiClientError,
  apiRequest,
  fetchFullMarketData,
  fetchIncrementalMarketData,
  generateStrategySignal,
  getBacktestDetail,
  getDashboard,
  getHealth,
  getLatestStrategySignal,
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
        new Response(JSON.stringify({ detail: "not found" }), {
          headers: { "Content-Type": "application/json" },
          status: 404
        })
      )
    );

    await expect(apiRequest("/missing")).rejects.toMatchObject({
      kind: "http",
      status: 404,
      message: "not found"
    });
  });

  it("normalizes network errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));

    await expect(apiRequest("/health")).rejects.toMatchObject({
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
      universe_config_path: "config/etf_universe.yaml",
      momentum_windows: [20, 60, 120],
      score_weights: [0.2, 0.3, 0.5],
      trend_filter: { enabled: true },
      selection: { top_n: 2 },
      defense_asset: { symbol: "BIL" },
      costs: { transaction_cost_bps: 5 },
      performance: { rebalance_frequency: "weekly" }
    },
    market_data: {
      price_rows: 1200,
      covered_etfs: 8,
      earliest_trade_date: "2025-01-02",
      latest_trade_date: "2026-06-23"
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
      strategy_name: "dual_momentum",
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

it("calls strategy signal generation through the shared client", async () => {
  const generateResult = {
    signal_id: 42,
    signal_date: "2026-06-23",
    config_version: "v1",
    status: "success",
    result: "rebalance",
    error_message: null,
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
      strategy_name: "dual_momentum",
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

it("exposes a typed API client error", () => {
  const error = new ApiClientError("HTTP request failed", { kind: "http", status: 500 });

  expect(error).toMatchObject({
    kind: "http",
    status: 500,
    message: "HTTP request failed"
  });
});
