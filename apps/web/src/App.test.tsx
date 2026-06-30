import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  const strategyPanel = screen.getByRole("heading", { name: "Strategy summary" }).closest("article");
  expect(strategyPanel).not.toBeNull();
  const strategy = within(strategyPanel as HTMLElement);
  expect(strategy.getByText("dual_momentum")).toBeInTheDocument();
  expect(strategy.getByText("v1")).toBeInTheDocument();
  expect(strategy.getByText("63 / 126 days")).toBeInTheDocument();
  expect(strategy.getByText("Short 0.4 / Long 0.6")).toBeInTheDocument();
  expect(strategy.getByText("2")).toBeInTheDocument();
  expect(strategy.getByText("SSE:511010")).toBeInTheDocument();
  expect(strategy.getByText("5 bps")).toBeInTheDocument();
  const signalPanel = screen.getByRole("heading", { name: "Latest signal" }).closest("article");
  expect(signalPanel).not.toBeNull();
  const signal = within(signalPanel as HTMLElement);
  expect(signal.getByText("Signal #42")).toBeInTheDocument();
  expect(signal.getByText("2026-06-23")).toBeInTheDocument();
  expect(signal.getByText("rebalance")).toBeInTheDocument();
  expect(signal.getByText("Yes")).toBeInTheDocument();
  expect(signal.getByText("2")).toBeInTheDocument();
  const backtestPanel = screen.getByRole("heading", { name: "Recent backtest" }).closest("article");
  expect(backtestPanel).not.toBeNull();
  const backtest = within(backtestPanel as HTMLElement);
  expect(backtest.getByText("Backtest #7")).toBeInTheDocument();
  expect(backtest.getByText("2026-01-01 to 2026-06-01")).toBeInTheDocument();
  expect(backtest.getByText("success")).toBeInTheDocument();
  expect(backtest.getByText("12.00%")).toBeInTheDocument();
  expect(backtest.getByText("-5.00%")).toBeInTheDocument();
  expect(backtest.getByText("1.100000")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Fetch market data" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Generate signal" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Run backtest" })).toBeDisabled();
  expect(screen.queryByRole("button", { name: /edit strategy|edit config/i })).not.toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /edit strategy|edit config/i })).not.toBeInTheDocument();
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

  expect(
    await screen.findByText("No successful local signal exists yet. Generate signal after market data is ready.")
  ).toBeInTheDocument();
  const signalPanel = screen.getByRole("heading", { name: "Latest signal" }).closest("article");
  expect(signalPanel).not.toBeNull();
  expect(within(signalPanel as HTMLElement).getByRole("button", { name: "Generate signal" })).toBeDisabled();
  expect(
    screen.getByText("No local backtest run exists yet. Run backtest after a signal is available.")
  ).toBeInTheDocument();
  const backtestPanel = screen.getByRole("heading", { name: "Recent backtest" }).closest("article");
  expect(backtestPanel).not.toBeNull();
  expect(within(backtestPanel as HTMLElement).getByRole("button", { name: "Run backtest" })).toBeDisabled();
  expect(screen.queryByText(/Dashboard API unavailable/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/login|sign up|account|team|deploy|production|hosting|remote/i)).not.toBeInTheDocument();
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

  expect(
    await screen.findByText("No local market prices are stored yet. Fetch market data to populate dashboard coverage.")
  ).toBeInTheDocument();
  const marketPanel = screen.getByRole("heading", { name: "Market data" }).closest("article");
  expect(marketPanel).not.toBeNull();
  expect(within(marketPanel as HTMLElement).getByRole("button", { name: "Fetch market data" })).toBeEnabled();
  expect(screen.getByText("0 rows")).toBeInTheDocument();
  expect(screen.getByText("0 ETFs")).toBeInTheDocument();
  expect(screen.queryByText(/Dashboard API unavailable/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/login|sign up|account|team|deploy|production|hosting|remote/i)).not.toBeInTheDocument();
});

it("keeps the dashboard layout visible when dashboard loading fails", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));

  render(<App />);

  expect(await screen.findByText("Dashboard API unavailable: network")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Workflow Dashboard" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Market data" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Operations" })).toBeInTheDocument();
});

it("triggers incremental market data fetch and refreshes dashboard data", async () => {
  const fetchResult = createDeferred<Response>();
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard" && fetchMock.mock.calls.length === 1) {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/market-data/fetch?mode=incremental") {
      return fetchResult.promise;
    }

    if (url === "/api/dashboard") {
      return Promise.resolve(
        jsonResponse({
          ...createDashboardResponse(),
          market_data: {
            price_rows: 1300,
            covered_etfs: 9,
            earliest_trade_date: "2025-01-02",
            latest_trade_date: "2026-06-24"
          }
        })
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  const button = await screen.findByRole("button", { name: "Fetch market data" });
  fireEvent.click(button);
  fireEvent.click(button);

  expect(await screen.findByRole("button", { name: "Fetching market data" })).toBeDisabled();
  expect(fetchMock).toHaveBeenCalledWith("/api/market-data/fetch?mode=incremental", {
    method: "POST"
  });
  expect(fetchMock.mock.calls.filter(([url]) => url === "/api/market-data/fetch?mode=incremental")).toHaveLength(1);

  fetchResult.resolve(
    jsonResponse({
      status: "success",
      requested_etf_count: 1,
      rows_fetched: 100,
      rows_inserted: 100,
      rows_updated: 0,
      failed_symbols: [],
      error_message: null
    })
  );

  expect(await screen.findByText("1,300 rows")).toBeInTheDocument();
  const operationsPanel = screen.getByRole("heading", { name: "Operations" }).closest("article");
  expect(operationsPanel).not.toBeNull();
  const operations = within(operationsPanel as HTMLElement);
  expect(operations.getByText("Market data fetch success")).toBeInTheDocument();
  expect(operations.getAllByText("100 rows")).toHaveLength(2);
  expect(operations.getByText("0 rows")).toBeInTheDocument();
  expect(operations.queryByText("Failed symbols")).not.toBeInTheDocument();
  expect(screen.getByText("9 ETFs")).toBeInTheDocument();
  expect(screen.getByText("2026-06-24")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Fetch market data" })).toBeEnabled();
});

it("shows partial market data fetch failed symbols and guidance", async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/market-data/fetch?mode=incremental") {
      return Promise.resolve(
        jsonResponse({
          status: "partial",
          requested_etf_count: 2,
          rows_fetched: 25,
          rows_inserted: 20,
          rows_updated: 5,
          failed_symbols: ["510300"],
          error_message: "1 symbol failed from provider"
        })
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "Fetch market data" }));

  expect(await screen.findByText("Market data fetch partial")).toBeInTheDocument();
  const operationsPanel = screen.getByRole("heading", { name: "Operations" }).closest("article");
  expect(operationsPanel).not.toBeNull();
  const operations = within(operationsPanel as HTMLElement);
  expect(operations.getByText("25 rows")).toBeInTheDocument();
  expect(operations.getByText("20 rows")).toBeInTheDocument();
  expect(operations.getByText("5 rows")).toBeInTheDocument();
  expect(operations.getByText("510300")).toBeInTheDocument();
  expect(operations.getByText("1 symbol failed from provider")).toBeInTheDocument();
  expect(
    operations.getByText("Retry the fetch after checking the data source availability and local ETF/data state.")
  ).toBeInTheDocument();
});

it("shows failed market data fetch details and guidance from the response body", async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/market-data/fetch?mode=incremental") {
      return Promise.resolve(
        jsonResponse({
          status: "failed",
          requested_etf_count: 2,
          rows_fetched: 0,
          rows_inserted: 0,
          rows_updated: 0,
          failed_symbols: ["510300", "511010"],
          error_message: "provider unavailable"
        })
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "Fetch market data" }));

  expect(await screen.findByText("Market data fetch failed")).toBeInTheDocument();
  const operationsPanel = screen.getByRole("heading", { name: "Operations" }).closest("article");
  expect(operationsPanel).not.toBeNull();
  const operations = within(operationsPanel as HTMLElement);
  expect(operations.getByText("510300, 511010")).toBeInTheDocument();
  expect(operations.getByText("provider unavailable")).toBeInTheDocument();
  expect(
    operations.getByText("Retry the fetch after checking the data source availability and local ETF/data state.")
  ).toBeInTheDocument();
});

it("shows an operation error when incremental market data fetch fails", async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/market-data/fetch?mode=incremental") {
      return Promise.resolve(
        new Response(JSON.stringify({ detail: "fetch failed" }), {
          headers: { "Content-Type": "application/json" },
          status: 500
        })
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "Fetch market data" }));

  expect(await screen.findByText("Market data fetch failed: http")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Fetch market data" })).toBeEnabled();
  await waitFor(() => {
    expect(fetchMock.mock.calls.filter(([url]) => url === "/api/dashboard")).toHaveLength(1);
  });
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
      universe_config: "config/etf_pool.yaml",
      momentum: {
        short_window_days: 63,
        long_window_days: 126
      },
      score_weights: {
        short: 0.4,
        long: 0.6
      },
      trend_filter: { enabled: true },
      selection: { top_n: 2 },
      defense: {
        asset: {
          exchange: "SSE",
          symbol: "511010"
        }
      },
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
      is_fallback: true,
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

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    status: 200
  });
}

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });

  return { promise, reject, resolve };
}
