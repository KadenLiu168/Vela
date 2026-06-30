import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiClientError,
  apiRequest,
  fetchFullMarketData,
  fetchIncrementalMarketData,
  getDashboard,
  getHealth
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

it("exposes a typed API client error", () => {
  const error = new ApiClientError("HTTP request failed", { kind: "http", status: 500 });

  expect(error).toMatchObject({
    kind: "http",
    status: 500,
    message: "HTTP request failed"
  });
});
