import { render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  window.history.pushState({}, "", "/");
  vi.unstubAllGlobals();
});

it("renders the workflow dashboard on the default route", () => {
  render(<App />);

  expect(screen.getByRole("heading", { name: "Workflow Dashboard" })).toBeInTheDocument();
  expect(screen.getByText("Local research workflow")).toBeInTheDocument();
});

it("loads dashboard aggregate data through the shared client", async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(createDashboardResponse()), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(await screen.findByText("1,200 rows")).toBeInTheDocument();
  expect(screen.getByText("8 ETFs")).toBeInTheDocument();
  expect(screen.getByText("dual_momentum")).toBeInTheDocument();
  expect(screen.getByText("Signal #42")).toBeInTheDocument();
  expect(screen.getByText("Backtest #7")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Fetch market data" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Generate signal" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Run backtest" })).toBeDisabled();
  expect(fetchMock).toHaveBeenCalledWith("/api/dashboard", undefined);
});

it("renders empty dashboard states without treating the response as a failure", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          ...createDashboardResponse(),
          latest_signal: null,
          recent_backtest: null
        }),
        {
          headers: { "Content-Type": "application/json" },
          status: 200
        }
      )
    )
  );

  render(<App />);

  expect(await screen.findByText("No signal has been generated yet.")).toBeInTheDocument();
  expect(screen.getByText("No backtest run has been recorded yet.")).toBeInTheDocument();
  expect(screen.queryByText(/Dashboard API unavailable/i)).not.toBeInTheDocument();
});

it("renders an explicit empty state when local market data is missing", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          ...createDashboardResponse(),
          market_data: {
            price_rows: 0,
            covered_etfs: 0,
            earliest_trade_date: null,
            latest_trade_date: null
          }
        }),
        {
          headers: { "Content-Type": "application/json" },
          status: 200
        }
      )
    )
  );

  render(<App />);

  expect(await screen.findByText("No local market data has been stored yet.")).toBeInTheDocument();
  expect(screen.getByText("0 rows")).toBeInTheDocument();
  expect(screen.getByText("0 ETFs")).toBeInTheDocument();
  expect(screen.queryByText(/Dashboard API unavailable/i)).not.toBeInTheDocument();
});

it("keeps the dashboard layout visible when dashboard loading fails", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));

  render(<App />);

  expect(await screen.findByText("Dashboard API unavailable: network")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Workflow Dashboard" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Market data" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Operations" })).toBeInTheDocument();
});

it("renders the signal detail placeholder route", () => {
  window.history.pushState({}, "", "/signals/demo-signal");

  render(<App />);

  expect(screen.getByRole("heading", { name: "Signal Detail" })).toBeInTheDocument();
  expect(screen.getByText("Signal ID: demo-signal")).toBeInTheDocument();
});

it("renders the backtest detail placeholder route", () => {
  window.history.pushState({}, "", "/backtests/demo-backtest");

  render(<App />);

  expect(screen.getByRole("heading", { name: "Backtest Detail" })).toBeInTheDocument();
  expect(screen.getByText("Backtest ID: demo-backtest")).toBeInTheDocument();
});

it("exposes local research navigation without production account entry points", () => {
  render(<App />);

  expect(screen.getByRole("link", { name: "Dashboard" })).toHaveAttribute("href", "/");
  expect(screen.getByRole("link", { name: "Signal Detail" })).toHaveAttribute(
    "href",
    "/signals/demo-signal"
  );
  expect(screen.getByRole("link", { name: "Backtest Detail" })).toHaveAttribute(
    "href",
    "/backtests/demo-backtest"
  );

  expect(screen.queryByText(/login|sign up|account|team|deploy|production/i)).not.toBeInTheDocument();
});

function createDashboardResponse() {
  return {
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
    }
  };
}
