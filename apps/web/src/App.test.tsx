import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";
import { indexFromX } from "./pages/etfTrendChart";

afterEach(() => {
  window.history.pushState({}, "", "/");
  vi.unstubAllGlobals();
});

it("renders the workflow dashboard on the default route", () => {
  render(<App />);

  expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  expect(screen.getByText("Local research workflow")).toBeInTheDocument();
});

it("keeps the AppShell brand out of the page heading outline", () => {
  render(<App />);

  const brand = screen.getByText("Vela Research");

  expect(brand).toBeInTheDocument();
  expect(brand).toHaveClass("app-brand-title");
  expect(brand.tagName).toBe("P");
  expect(screen.queryByRole("heading", { name: "Vela Research" })).not.toBeInTheDocument();
  expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  expect(screen.getByRole("heading", { level: 1, name: "Dashboard" })).toBeInTheDocument();
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

  expect(await screen.findByText("Dashboard loaded")).toBeInTheDocument();
  expect(await screen.findByText("1,200 rows")).toBeInTheDocument();
  expect(screen.getByText("8 ETFs")).toBeInTheDocument();
  const marketPanel = screen.getByRole("heading", { name: "Market data" }).closest("article");
  expect(marketPanel).not.toBeNull();
  const market = within(marketPanel as HTMLElement);
  expect(market.getByText("Price rows")).toBeInTheDocument();
  expect(market.getByText("1,200 rows")).toBeInTheDocument();
  expect(market.getByText("Covered ETFs")).toBeInTheDocument();
  expect(market.getByText("8 ETFs")).toBeInTheDocument();
  expect(market.getByText("Earliest")).toBeInTheDocument();
  expect(market.getByText("2025-01-02")).toBeInTheDocument();
  expect(market.getByText("Latest")).toBeInTheDocument();
  expect(market.getByText("2026-06-23")).toBeInTheDocument();
  expect(market.getByText("SPY")).toBeInTheDocument();
  expect(market.getByText("SPY ETF")).toBeInTheDocument();
  expect(market.getByText("QQQ")).toBeInTheDocument();
  expect(market.getByText("QQQ ETF")).toBeInTheDocument();
  const strategyPanel = screen.getByRole("heading", { name: "Strategy" }).closest("article");
  expect(strategyPanel).not.toBeNull();
  const strategy = within(strategyPanel as HTMLElement);
  expect(strategy.getByText("dual_momentum")).toBeInTheDocument();
  expect(strategy.getByText("v1")).toBeInTheDocument();
  expect(strategy.getByText("63 / 126 days")).toBeInTheDocument();
  expect(strategy.getByText("Short 0.4 / Long 0.6")).toBeInTheDocument();
  expect(strategy.getByText("2")).toBeInTheDocument();
  expect(strategy.getByText("SSE:511010")).toBeInTheDocument();
  expect(strategy.getByText("5 bps")).toBeInTheDocument();
  const signalPanel = screen.getByTestId("workflow-panel-signal");
  expect(signalPanel).not.toBeNull();
  const signal = within(signalPanel as HTMLElement);
  expect(signal.getByText("Signal #42")).toBeInTheDocument();
  expect(signal.getByText("2026-06-23")).toBeInTheDocument();
  expect(signal.getByText("success")).toBeInTheDocument();
  expect(signal.getByText("rebalance")).toBeInTheDocument();
  expect(signal.getByText("Yes")).toBeInTheDocument();
  expect(signal.getByText("2")).toBeInTheDocument();
  expect(signal.getByRole("link", { name: "View signal detail" })).toHaveAttribute(
    "href",
    "/signals/42"
  );
  const backtestPanel = screen.getByTestId("workflow-panel-backtest");
  expect(backtestPanel).not.toBeNull();
  const backtest = within(backtestPanel as HTMLElement);
  expect(backtest.getByText("Backtest #7")).toBeInTheDocument();
  expect(backtest.getByText("2026-01-01 to 2026-06-01")).toBeInTheDocument();
  expect(backtest.getByText("success")).toBeInTheDocument();
  expect(backtest.getByText("12.00%")).toBeInTheDocument();
  expect(backtest.getByText("-5.00%")).toBeInTheDocument();
  expect(backtest.getByText("1.100000")).toBeInTheDocument();
  expect(backtest.getByRole("link", { name: "View backtest detail" })).toHaveAttribute(
    "href",
    "/backtests/7"
  );
  const fetchLogPanel = screen.getByRole("heading", { name: "Data fetches" }).closest("article");
  expect(fetchLogPanel).not.toBeNull();
  const fetchLogs = within(fetchLogPanel as HTMLElement);
  const firstFetchLog = within((fetchLogPanel as HTMLElement).querySelector(".fetch-log-entry") as HTMLElement);
  expect(firstFetchLog.getByText("2026-06-24T08:00:00")).toBeInTheDocument();
  expect(firstFetchLog.getByText("Fetched 25 rows · Inserted 20 rows · Updated 5 rows")).toBeInTheDocument();
  const firstEntryStatus = firstFetchLog.getByText("Partial");
  expect(firstEntryStatus).toHaveClass("status-pill-partial");
  const firstEntryError = firstFetchLog.getByText("QQQ: provider timeout");
  expect(firstEntryError).not.toBeVisible();
  const firstEntryElement = (fetchLogPanel as HTMLElement).querySelector(".fetch-log-entry") as HTMLElement;
  const firstEntrySummary = within(firstEntryElement).getByText("Show error");
  fireEvent.click(firstEntrySummary);
  expect(within(firstEntryElement).getByText("QQQ: provider timeout")).toBeVisible();
  expect(fetchLogs.getByText("2026-06-23T07:05:00")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Fetch market data" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Bootstrap / Setup database & data" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Generate signal" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "Run backtest" })).toBeEnabled();
  expect(screen.queryByRole("button", { name: /edit strategy|edit config/i })).not.toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /edit strategy|edit config/i })).not.toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith("/api/dashboard", undefined);
});

it("renders shared page loading feedback while dashboard data is pending", () => {
  const dashboardResult = createDeferred<Response>();
  vi.stubGlobal("fetch", vi.fn().mockReturnValue(dashboardResult.promise));

  render(<App />);

  const loadingFeedback = screen.getByRole("status", { name: "" });
  expect(loadingFeedback).toHaveTextContent("Loading dashboard data.");
  expect(loadingFeedback).toHaveClass("status-surface", "feedback-message", "feedback-message-loading");
  expect(screen.getByText("Loading dashboard")).toHaveClass(
    "status-surface",
    "dashboard-load-state",
    "dashboard-load-state-loading"
  );
  expect(screen.queryByText("1,200 rows")).not.toBeInTheDocument();
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

  const signalEmptyState = await screen.findByText(
    "No successful local signal exists yet. Generate signal after market data is ready."
  );
  expect(signalEmptyState).toBeInTheDocument();
  expect(signalEmptyState).toHaveClass("status-surface", "status-surface-empty", "empty-state");
  const signalPanel = screen.getByTestId("workflow-panel-signal");
  expect(signalPanel).not.toBeNull();
  expect(within(signalPanel as HTMLElement).getByRole("button", { name: "Generate signal" })).toBeEnabled();
  expect(
    screen.getByText("No local backtest run exists yet. Enter a date range in Operations, then run a backtest.")
  ).toBeInTheDocument();
  const backtestPanel = screen.getByTestId("workflow-panel-backtest");
  expect(backtestPanel).not.toBeNull();
  expect(
    within(backtestPanel as HTMLElement).queryByRole("button", { name: "Run backtest" })
  ).not.toBeInTheDocument();
  expect(screen.queryByText(/Dashboard API unavailable/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/login|sign up|account|team|deploy|production|hosting|remote/i)).not.toBeInTheDocument();
});

it("renders an empty fetch history state without treating the response as a failure", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          ...createDashboardResponse(),
          recent_fetch_logs: []
        }),
        {
          headers: { "Content-Type": "application/json" },
          status: 200
        }
      )
    )
  );

  render(<App />);

  expect(await screen.findByText("No market data fetch history exists yet.")).toBeInTheDocument();
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
            latest_trade_date: null,
            etf_list: [],
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
  expect(screen.getByRole("heading", { name: "First run setup" })).toBeInTheDocument();
  expect(
    screen.getByText("No local market data is available yet. Fetch market data to start using the dashboard.")
  ).toBeInTheDocument();
  const marketPanel = screen.getByRole("heading", { name: "Market data" }).closest("article");
  expect(marketPanel).not.toBeNull();
  expect(within(marketPanel as HTMLElement).getByRole("button", { name: "Fetch market data" })).toBeEnabled();
  expect(screen.getAllByRole("button", { name: "Fetch market data" })).toHaveLength(2);
  expect(screen.getByText("0 rows")).toBeInTheDocument();
  expect(screen.getByText("0 ETFs")).toBeInTheDocument();
  expect(within(marketPanel as HTMLElement).queryAllByText("n/a")).toHaveLength(0);
  expect(within(marketPanel as HTMLElement).queryByText("SPY")).not.toBeInTheDocument();
  expect(screen.queryByText(/Dashboard API unavailable/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/login|sign up|account|team|deploy|production|hosting|remote/i)).not.toBeInTheDocument();
});

it("keeps the dashboard layout visible when dashboard loading fails", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));

  render(<App />);

  expect(await screen.findByText("Dashboard API unavailable: network")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "First run setup" })).toBeInTheDocument();
  expect(
    screen.getByText("Run vela init-db to initialize the local database, then fetch market data.")
  ).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Market data" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Operations" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Fetch market data" })).toBeEnabled();
  expect(screen.queryByText(/login|sign up|account|team|deploy|production|hosting|remote/i)).not.toBeInTheDocument();
});

it("does not render first-run guidance after local market data exists", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(createDashboardResponse())));

  render(<App />);

  expect(await screen.findByText("1,200 rows")).toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: "First run setup" })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Fetch market data" })).toBeEnabled();
});

it("manually refreshes Dashboard status from the shared Dashboard API", async () => {
  let dashboardRequestCount = 0;
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      dashboardRequestCount += 1;
      return Promise.resolve(
        jsonResponse({
          ...createDashboardResponse(),
          market_data: {
            price_rows: dashboardRequestCount === 1 ? 1200 : 1450,
            covered_etfs: dashboardRequestCount === 1 ? 8 : 9,
            earliest_trade_date: "2025-01-02",
            latest_trade_date: dashboardRequestCount === 1 ? "2026-06-23" : "2026-06-25",
            etf_list: [
              { exchange: "NYSEARCA", symbol: "SPY", name: "SPY ETF", category: "equity_us" },
              { exchange: "NYSEARCA", symbol: "QQQ", name: "QQQ ETF", category: "equity_us_tech" },
            ],
          }
        })
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(await screen.findByText("1,200 rows")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Refresh Dashboard" }));

  expect(await screen.findByText("1,450 rows")).toBeInTheDocument();
  expect(screen.getByText("9 ETFs")).toBeInTheDocument();
  expect(screen.getByText("2026-06-25")).toBeInTheDocument();
  expect(fetchMock.mock.calls.filter(([url]) => url === "/api/dashboard")).toHaveLength(2);
});

it("derives Signal panel status pill from signal state", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(jsonResponse(createDashboardResponse()))
  );

  render(<App />);

  const signalPanel = await screen.findByTestId("workflow-panel-signal");
  const signalPill = (signalPanel as HTMLElement).querySelector(".panel-heading-end .status-pill");
  expect(signalPill).not.toBeNull();
  expect(signalPill).toHaveTextContent("Active");
  expect(signalPill).toHaveClass("status-pill-success");
});

it("renders Signal panel status pill as No data when the signal is missing", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      jsonResponse({
        ...createDashboardResponse(),
        latest_signal: null
      })
    )
  );

  render(<App />);

  const signalPanel = await screen.findByTestId("workflow-panel-signal");
  const signalPill = (signalPanel as HTMLElement).querySelector(".panel-heading-end .status-pill");
  expect(signalPill).not.toBeNull();
  expect(signalPill).toHaveTextContent("No data");
  expect(signalPill).toHaveClass("status-pill-neutral");
});

it("derives Backtest panel status pill from recent backtest state", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(jsonResponse(createDashboardResponse()))
  );

  render(<App />);

  const backtestPanel = await screen.findByTestId("workflow-panel-backtest");
  const backtestPill = (backtestPanel as HTMLElement).querySelector(".panel-heading-end .status-pill");
  expect(backtestPill).not.toBeNull();
  expect(backtestPill).toHaveTextContent("Active");
  expect(backtestPill).toHaveClass("status-pill-success");
});

it("renders Backtest panel status pill as No data when the backtest is missing", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      jsonResponse({
        ...createDashboardResponse(),
        recent_backtest: null
      })
    )
  );

  render(<App />);

  const backtestPanel = await screen.findByTestId("workflow-panel-backtest");
  const backtestPill = (backtestPanel as HTMLElement).querySelector(".panel-heading-end .status-pill");
  expect(backtestPill).not.toBeNull();
  expect(backtestPill).toHaveTextContent("No data");
  expect(backtestPill).toHaveClass("status-pill-neutral");
});

it("derives Fetches panel status pill from the latest log row", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(jsonResponse(createDashboardResponse()))
  );

  render(<App />);

  const fetchesPanel = await screen.findByTestId("workflow-panel-fetches");
  const fetchesPill = (fetchesPanel as HTMLElement).querySelector(".panel-heading-end .status-pill");
  expect(fetchesPill).not.toBeNull();
  expect(fetchesPill).toHaveTextContent("Partial");
  expect(fetchesPill).toHaveClass("status-pill-partial");
});

it("renders Fetches panel status pill as Errors when the latest log is failed", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      jsonResponse({
        ...createDashboardResponse(),
        recent_fetch_logs: [
          {
            fetch_log_id: 12,
            fetch_time: "2026-06-25T08:00:00",
            mode: "full",
            status: "failed",
            rows_fetched: 0,
            rows_inserted: 0,
            rows_updated: 0,
            error_summary: "all symbols failed"
          }
        ]
      })
    )
  );

  render(<App />);

  const fetchesPanel = await screen.findByTestId("workflow-panel-fetches");
  const fetchesPill = (fetchesPanel as HTMLElement).querySelector(".panel-heading-end .status-pill");
  expect(fetchesPill).not.toBeNull();
  expect(fetchesPill).toHaveTextContent("Errors");
  expect(fetchesPill).toHaveClass("status-pill-error");
});

it("renders Fetches panel status pill as No data when the log list is empty", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      jsonResponse({
        ...createDashboardResponse(),
        recent_fetch_logs: []
      })
    )
  );

  render(<App />);

  const fetchesPanel = await screen.findByTestId("workflow-panel-fetches");
  const fetchesPill = (fetchesPanel as HTMLElement).querySelector(".panel-heading-end .status-pill");
  expect(fetchesPill).not.toBeNull();
  expect(fetchesPill).toHaveTextContent("No data");
  expect(fetchesPill).toHaveClass("status-pill-neutral");
});

it("keeps the fetch log error text hidden until the disclosure is expanded", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(jsonResponse(createDashboardResponse()))
  );

  render(<App />);

  const fetchesPanel = await screen.findByTestId("workflow-panel-fetches");
  const errorText = within(fetchesPanel as HTMLElement).getByText("QQQ: provider timeout");
  expect(errorText).not.toBeVisible();

  const summary = within(fetchesPanel as HTMLElement).getByText("Show error");
  fireEvent.click(summary);

  expect(within(fetchesPanel as HTMLElement).getByText("QQQ: provider timeout")).toBeVisible();
});

it("presents full market data fetch after the incremental fetch action", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(createDashboardResponse())));

  render(<App />);

  await screen.findByText("1,200 rows");
  const operationsPanel = screen.getByRole("heading", { name: "Operations" }).closest("article");
  expect(operationsPanel).not.toBeNull();
  const actions = within(operationsPanel as HTMLElement).getAllByRole("button");

  expect(actions.map((button) => button.textContent)).toEqual([
    "Fetch market data",
    "Generate signal",
    "Bootstrap / Setup database & data",
    "Run backtest"
  ]);
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
            latest_trade_date: "2026-06-24",
            etf_list: [
              { exchange: "NYSEARCA", symbol: "SPY", name: "SPY ETF", category: "equity_us" },
              { exchange: "NYSEARCA", symbol: "QQQ", name: "QQQ ETF", category: "equity_us_tech" },
            ],
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
  expect(screen.getByRole("status", { name: "" })).toHaveTextContent("Fetching market data.");
  expect(screen.getByRole("button", { name: "Bootstrap / Setup database & data" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Generate signal" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Run backtest" })).toBeDisabled();
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

it("keeps market data fetch success visible when the follow-up Dashboard refresh fails", async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard" && fetchMock.mock.calls.length === 1) {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/market-data/fetch?mode=incremental") {
      return Promise.resolve(
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
    }

    if (url === "/api/dashboard") {
      return Promise.reject(new TypeError("failed"));
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "Fetch market data" }));

  expect(await screen.findByText("Market data fetch success")).toBeInTheDocument();
  expect(screen.getByText("Dashboard API unavailable: network")).toBeInTheDocument();
  expect(screen.queryByText("Market data fetch failed")).not.toBeInTheDocument();
  expect(fetchMock.mock.calls.filter(([url]) => url === "/api/dashboard")).toHaveLength(2);
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

it("triggers bootstrap and displays three-step status", async () => {
  const bootstrapResult = createDeferred<Response>();
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard" && fetchMock.mock.calls.length === 1) {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/setup/bootstrap") {
      return bootstrapResult.promise;
    }

    if (url === "/api/dashboard") {
      return Promise.resolve(
        jsonResponse({
          ...createDashboardResponse(),
          market_data: {
            price_rows: 2400,
            covered_etfs: 9,
            earliest_trade_date: "2024-01-02",
            latest_trade_date: "2026-06-24",
            etf_list: [
              { exchange: "NYSEARCA", symbol: "SPY", name: "SPY ETF", category: "equity_us" },
              { exchange: "NYSEARCA", symbol: "QQQ", name: "QQQ ETF", category: "equity_us_tech" },
            ],
          }
        })
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  const button = await screen.findByRole("button", { name: "Bootstrap / Setup database & data" });
  fireEvent.click(button);
  fireEvent.click(button);

  expect(await screen.findByRole("button", { name: "Running bootstrap" })).toBeDisabled();
  expect(screen.getByRole("status", { name: "" })).toHaveTextContent("Running local setup bootstrap.");
  expect(screen.getByRole("button", { name: "Fetch market data" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Generate signal" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Run backtest" })).toBeDisabled();
  expect(fetchMock).toHaveBeenCalledWith("/api/setup/bootstrap", {
    method: "POST"
  });
  expect(fetchMock.mock.calls.filter(([url]) => url === "/api/setup/bootstrap")).toHaveLength(1);

  bootstrapResult.resolve(
    jsonResponse({
      status: "success",
      failed_step: null,
      total_duration_seconds: 0.5,
      steps: [
        { name: "migrate", status: "success", duration_seconds: 0.1, error_message: null },
        { name: "sync_etf_pool", status: "success", duration_seconds: 0.2, error_message: null },
        { name: "fetch_full_market_data", status: "success", duration_seconds: 0.2, error_message: null }
      ]
    })
  );

  expect(await screen.findByText("2,400 rows")).toBeInTheDocument();
  const operationsPanel = screen.getByRole("heading", { name: "Operations" }).closest("article");
  expect(operationsPanel).not.toBeNull();
  const operations = within(operationsPanel as HTMLElement);
  expect(operations.getByText("Bootstrap success")).toBeInTheDocument();
  expect(operations.getByText("Total duration: 0.5s")).toBeInTheDocument();
  expect(operations.getByText("✓ Migrate")).toBeInTheDocument();
  expect(operations.getByText("✓ Sync ETF pool")).toBeInTheDocument();
  expect(operations.getByText("✓ Fetch full market data")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Bootstrap / Setup database & data" })).toBeEnabled();
});

it("shows failed bootstrap status with error message on the failing step", async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/setup/bootstrap") {
      return Promise.resolve(
        jsonResponse({
          status: "failed",
          failed_step: "sync_etf_pool",
          total_duration_seconds: 1.2,
          steps: [
            { name: "migrate", status: "success", duration_seconds: 0.1, error_message: null },
            { name: "sync_etf_pool", status: "failed", duration_seconds: 0.1, error_message: "ETF pool config missing" },
            { name: "fetch_full_market_data", status: "success", duration_seconds: 1.0, error_message: null }
          ]
        })
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "Bootstrap / Setup database & data" }));

  expect(await screen.findByText("Bootstrap failed")).toBeInTheDocument();
  const operationsPanel = screen.getByRole("heading", { name: "Operations" }).closest("article");
  expect(operationsPanel).not.toBeNull();
  const operations = within(operationsPanel as HTMLElement);
  expect(operations.getByText("Total duration: 1.2s")).toBeInTheDocument();
  expect(operations.getByText("✓ Migrate")).toBeInTheDocument();
  expect(operations.getByText("✗ Sync ETF pool")).toBeInTheDocument();
  expect(operations.getByText("ETF pool config missing")).toBeInTheDocument();
  expect(
    operations.getByText("Fix the reported issue in sync_etf_pool and re-run the bootstrap action.")
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

it("shows a market data fetch error summary with reason and next step", async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/market-data/fetch?mode=incremental") {
      return Promise.resolve(
        new Response(JSON.stringify({ detail: "Tencent provider timed out while fetching 510300" }), {
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

  expect(await screen.findByText("Market data fetch failed")).toBeInTheDocument();
  const operationsPanel = screen.getByRole("heading", { name: "Operations" }).closest("article");
  expect(operationsPanel).not.toBeNull();
  const operations = within(operationsPanel as HTMLElement);
  expect(operations.getByText("Type")).toBeInTheDocument();
  expect(operations.getByText("Unexpected")).toBeInTheDocument();
  expect(operations.getByText("Reason")).toBeInTheDocument();
  expect(operations.getByText("Tencent provider timed out while fetching 510300")).toBeInTheDocument();
  expect(operations.getByText("Next step")).toBeInTheDocument();
  expect(
    operations.getByText("Retry after checking data source availability and local ETF/data state.")
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Fetch market data" })).toBeEnabled();
  await waitFor(() => {
    expect(fetchMock.mock.calls.filter(([url]) => url === "/api/dashboard")).toHaveLength(1);
  });
});

it("triggers signal generation and refreshes latest signal data", async () => {
  const generateResult = createDeferred<Response>();
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard" && fetchMock.mock.calls.length === 1) {
      return Promise.resolve(
        jsonResponse({
          ...createDashboardResponse(),
          latest_signal: null
        })
      );
    }

    if (url === "/api/strategy-signals/generate") {
      return generateResult.promise;
    }

    if (url === "/api/dashboard") {
      return Promise.resolve(
        jsonResponse({
          ...createDashboardResponse(),
          latest_signal: null
        })
      );
    }

    if (url === "/api/strategy-signals/latest") {
      return Promise.resolve(jsonResponse(createGeneratedLatestSignalResponse()));
    }

    if (url === "/api/strategy-signals?limit=20&offset=0") {
      return Promise.resolve(
        jsonResponse({
          signals: [
            {
              signal_id: 43,
              signal_date: "2026-06-24",
              config_version: "v1",
              result: "rebalance",
              generated_at: "2026-06-24T09:30:00",
              is_fallback: false,
              position_count: 2
            }
          ]
        })
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  const signalArticle = await screen.findByTestId("workflow-panel-signal");
  expect(signalArticle).not.toBeNull();
  const button = within(signalArticle as HTMLElement).getByRole("button", { name: "Generate signal" });
  fireEvent.click(button);
  fireEvent.click(button);

  expect(await within(signalArticle as HTMLElement).findByRole("button", { name: "Generating signal" })).toBeDisabled();
  expect(screen.getByRole("status", { name: "" })).toHaveTextContent("Generating latest strategy signal.");
  expect(screen.getByRole("button", { name: "Fetch market data" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Bootstrap / Setup database & data" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Run backtest" })).toBeDisabled();
  expect(fetchMock).toHaveBeenCalledWith("/api/strategy-signals/generate", {
    method: "POST"
  });
  expect(fetchMock.mock.calls.filter(([url]) => url === "/api/strategy-signals/generate")).toHaveLength(1);

  generateResult.resolve(
    jsonResponse({
      signal_id: 43,
      signal_date: "2026-06-24",
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
        },
        {
          etf_id: 2,
          exchange: "SZSE",
          symbol: "159915",
          target_weight: "0.500000",
          rank: 2,
          score: "0.700000"
        }
      ]
    })
  );

  expect(await within(signalArticle as HTMLElement).findByText("Signal #43")).toBeInTheDocument();
  expect(within(signalArticle as HTMLElement).getByText("2026-06-24")).toBeInTheDocument();
  expect(within(signalArticle as HTMLElement).getByText("No")).toBeInTheDocument();
  expect(fetchMock.mock.calls.filter(([url]) => url === "/api/dashboard")).toHaveLength(2);
  expect(fetchMock.mock.calls.filter(([url]) => url === "/api/strategy-signals/latest")).toHaveLength(1);
  const operationsPanel = screen.getByRole("heading", { name: "Operations" }).closest("article");
  expect(operationsPanel).not.toBeNull();
  const operations = within(operationsPanel as HTMLElement);
  expect(operations.getByText("Signal generation success")).toBeInTheDocument();
  expect(operations.getByText("#43")).toBeInTheDocument();
  expect(operations.getByText("2")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Generate signal" })).toBeEnabled();

  fireEvent.click(screen.getByRole("link", { name: "Signals" }));

  expect(await screen.findByRole("heading", { name: "Signals" })).toBeInTheDocument();
  expect(await screen.findByRole("link", { name: "#43" })).toHaveAttribute("href", "/signals/43");
  expect(screen.getByText("2026-06-24")).toBeInTheDocument();
  expect(screen.getByText("rebalance")).toBeInTheDocument();
  expect(
    fetchMock.mock.calls.filter(([url]) => url === "/api/strategy-signals?limit=20&offset=0")
  ).toHaveLength(1);
});

it("restores Dashboard latest signal status from backend data after browser refresh", async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      return Promise.resolve(
        jsonResponse({
          ...createDashboardResponse(),
          latest_signal: {
            signal_id: 43,
            signal_date: "2026-06-24",
            config_version: "v1",
            status: "success",
            result: "rebalance",
            generated_at: "2026-06-24T09:30:00",
            is_fallback: false,
            position_count: 2
          }
        })
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  const signalArticle = await screen.findByTestId("workflow-panel-signal");
  expect(signalArticle).not.toBeNull();
  const signal = within(signalArticle as HTMLElement);
  expect(await signal.findByText("Signal #43")).toBeInTheDocument();
  expect(signal.getByText("2026-06-24")).toBeInTheDocument();
  expect(signal.getByText("rebalance")).toBeInTheDocument();
  expect(signal.getByText("No")).toBeInTheDocument();
  expect(signal.getByText("2")).toBeInTheDocument();
  expect(signal.getByRole("link", { name: "View signal detail" })).toHaveAttribute(
    "href",
    "/signals/43"
  );
  expect(screen.queryByText(/Signal generation success/i)).not.toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith("/api/dashboard", undefined);
});

it("shows a signal generation error summary with reason and next step", async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/strategy-signals/generate") {
      return Promise.resolve(
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
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "Generate signal" }));

  expect(await screen.findByText("Signal generation failed")).toBeInTheDocument();
  const operationsPanel = screen.getByRole("heading", { name: "Operations" }).closest("article");
  expect(operationsPanel).not.toBeNull();
  const operations = within(operationsPanel as HTMLElement);
  expect(operations.getByRole("alert")).toHaveTextContent("Signal generation failed");
  expect(operations.getByText("Type")).toBeInTheDocument();
  expect(operations.getByText("Operation failed")).toBeInTheDocument();
  expect(operations.getByText("Reason")).toBeInTheDocument();
  expect(operations.getByText("No local market prices found")).toBeInTheDocument();
  expect(operations.getByText("Next step")).toBeInTheDocument();
  expect(
    operations.getByText("Fetch market data or review local strategy configuration before retrying.")
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Generate signal" })).toBeEnabled();
  await waitFor(() => {
    expect(fetchMock.mock.calls.filter(([url]) => url === "/api/dashboard")).toHaveLength(1);
  });
});

it("pairs technical operation error details with user guidance", async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/strategy-signals/generate") {
      return Promise.resolve(
        new Response(JSON.stringify({ detail: "sqlalchemy.exc.OperationalError: database is locked" }), {
          headers: { "Content-Type": "application/json" },
          status: 500
        })
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "Generate signal" }));

  expect(await screen.findByText("Signal generation failed")).toBeInTheDocument();
  const operationsPanel = screen.getByRole("heading", { name: "Operations" }).closest("article");
  expect(operationsPanel).not.toBeNull();
  const operations = within(operationsPanel as HTMLElement);
  expect(operations.getByText("sqlalchemy.exc.OperationalError: database is locked")).toBeInTheDocument();
  expect(
    operations.getByText("Fetch market data or review local strategy configuration before retrying.")
  ).toBeInTheDocument();
});

it("submits a Dashboard backtest date range through the shared API", async () => {
  let dashboardRequestCount = 0;
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      dashboardRequestCount += 1;
      return Promise.resolve(
        jsonResponse({
          ...createDashboardResponse(),
          recent_backtest:
            dashboardRequestCount === 1
              ? null
              : {
                  run_id: 8,
                  strategy_id: "dual_momentum",
                  config_version: "v1",
                  start_date: "2026-01-01",
                  end_date: "2026-01-31",
                  status: "success",
                  total_return: "0.120000",
                  max_drawdown: "-0.050000",
                  sharpe_ratio: "1.100000",
                  started_at: "2026-06-25T09:00:00"
                }
        })
      );
    }

    if (url === "/api/backtests/run?startDate=2026-01-01&endDate=2026-01-31") {
      return Promise.resolve(jsonResponse(createBacktestRunResponse()));
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  await screen.findByText("1,200 rows");
  expect(
    screen.getByText("No local backtest run exists yet. Enter a date range in Operations, then run a backtest.")
  ).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-01-01" } });
  fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-01-31" } });
  fireEvent.click(screen.getByRole("button", { name: "Run backtest" }));

  expect(await screen.findByText("Backtest run success")).toBeInTheDocument();
  const operationsPanel = screen.getByRole("heading", { name: "Operations" }).closest("article");
  expect(operationsPanel).not.toBeNull();
  const operations = within(operationsPanel as HTMLElement);
  expect(operations.getByText("#8")).toBeInTheDocument();
  expect(operations.getByText("21")).toBeInTheDocument();
  expect(operations.getByText("5")).toBeInTheDocument();
  expect(operations.getByText("12.00%")).toBeInTheDocument();
  expect(operations.getByText("144.00%")).toBeInTheDocument();
  expect(operations.getByText("-5.00%")).toBeInTheDocument();
  expect(operations.getByText("20.00%")).toBeInTheDocument();
  expect(operations.getByText("1.100000")).toBeInTheDocument();
  expect(operations.getByRole("link", { name: "View backtest detail" })).toHaveAttribute(
    "href",
    "/backtests/8"
  );
  const backtestPanel = screen.getByTestId("workflow-panel-backtest");
  expect(backtestPanel).not.toBeNull();
  const recentBacktest = within(backtestPanel as HTMLElement);
  expect(await recentBacktest.findByText("Backtest #8")).toBeInTheDocument();
  expect(recentBacktest.getByText("2026-01-01 to 2026-01-31")).toBeInTheDocument();
  expect(recentBacktest.getByText("success")).toBeInTheDocument();
  expect(dashboardRequestCount).toBe(2);
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/backtests/run?startDate=2026-01-01&endDate=2026-01-31",
    {
      method: "POST"
    }
  );
});

it("validates Dashboard backtest dates before submitting", async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  await screen.findByText("1,200 rows");
  fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-99-01" } });
  fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-01-31" } });
  fireEvent.click(screen.getByRole("button", { name: "Run backtest" }));

  expect(await screen.findByText("Enter dates in YYYY-MM-DD format.")).toBeInTheDocument();
  expect(fetchMock.mock.calls.filter(([url]) => String(url).startsWith("/api/backtests/run"))).toHaveLength(0);

  fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-02-01" } });
  fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-01-31" } });
  fireEvent.click(screen.getByRole("button", { name: "Run backtest" }));

  expect(await screen.findByText("Start date must be on or before end date.")).toBeInTheDocument();
  expect(fetchMock.mock.calls.filter(([url]) => String(url).startsWith("/api/backtests/run"))).toHaveLength(0);
});

it("prevents duplicate Dashboard backtest submissions while pending", async () => {
  const backtestResult = createDeferred<Response>();
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/backtests/run?startDate=2026-01-01&endDate=2026-01-31") {
      return backtestResult.promise;
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  await screen.findByText("1,200 rows");
  fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-01-01" } });
  fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-01-31" } });
  const button = screen.getByRole("button", { name: "Run backtest" });
  fireEvent.click(button);
  fireEvent.click(button);

  expect(await screen.findByRole("button", { name: "Running backtest" })).toBeDisabled();
  expect(screen.getByRole("status", { name: "" })).toHaveTextContent("Running backtest.");
  expect(screen.getByRole("button", { name: "Fetch market data" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Bootstrap / Setup database & data" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Generate signal" })).toBeDisabled();
  expect(fetchMock.mock.calls.filter(([url]) => String(url).startsWith("/api/backtests/run"))).toHaveLength(1);

  backtestResult.resolve(jsonResponse(createBacktestRunResponse()));

  expect(await screen.findByText("Backtest run success")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Run backtest" })).toBeEnabled();
});

it("clears a prior Dashboard backtest summary when a later run fails", async () => {
  let backtestRequestCount = 0;
  let dashboardRequestCount = 0;
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      dashboardRequestCount += 1;
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/backtests/run?startDate=2026-01-01&endDate=2026-01-31") {
      backtestRequestCount += 1;

      if (backtestRequestCount === 1) {
        return Promise.resolve(jsonResponse(createBacktestRunResponse()));
      }

      return Promise.resolve(
        new Response(
          JSON.stringify({
            error: {
              code: "operation_failed",
              category: "operation_failed",
              message: "not enough signals"
            }
          }),
          {
            headers: { "Content-Type": "application/json" },
            status: 400
          }
        )
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  await screen.findByText("1,200 rows");
  fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-01-01" } });
  fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-01-31" } });
  fireEvent.click(screen.getByRole("button", { name: "Run backtest" }));

  expect(await screen.findByText("Backtest run success")).toBeInTheDocument();
  await waitFor(() => {
    expect(dashboardRequestCount).toBe(2);
  });

  fireEvent.click(screen.getByRole("button", { name: "Run backtest" }));

  expect(await screen.findByText("Backtest run failed")).toBeInTheDocument();
  const operationsPanel = screen.getByRole("heading", { name: "Operations" }).closest("article");
  expect(operationsPanel).not.toBeNull();
  const operations = within(operationsPanel as HTMLElement);
  expect(operations.getByText("Type")).toBeInTheDocument();
  expect(operations.getByText("Operation failed")).toBeInTheDocument();
  expect(operations.getByText("Reason")).toBeInTheDocument();
  expect(operations.getByText("not enough signals")).toBeInTheDocument();
  expect(operations.getByText("Next step")).toBeInTheDocument();
  expect(
    operations.getByText("Verify the date range and available local market data or signals before retrying.")
  ).toBeInTheDocument();
  expect(screen.queryByText("Backtest run success")).not.toBeInTheDocument();
  expect(within(operationsPanel as HTMLElement).queryByRole("link", { name: "View backtest detail" })).not.toBeInTheDocument();
  const backtestPanel = screen.getByTestId("workflow-panel-backtest");
  expect(backtestPanel).not.toBeNull();
  expect(within(backtestPanel as HTMLElement).getByRole("link", { name: "View backtest detail" })).toHaveAttribute(
    "href",
    "/backtests/7"
  );
  expect(dashboardRequestCount).toBe(2);
});

it("restores Dashboard recent backtest status from backend data after browser refresh", async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  const backtestPanel = screen.getByTestId("workflow-panel-backtest");
  expect(backtestPanel).not.toBeNull();
  const backtest = within(backtestPanel as HTMLElement);
  expect(await backtest.findByText("Backtest #7")).toBeInTheDocument();
  expect(backtest.getByText("2026-01-01 to 2026-06-01")).toBeInTheDocument();
  expect(backtest.getByText("success")).toBeInTheDocument();
  expect(backtest.getByRole("link", { name: "View backtest detail" })).toHaveAttribute(
    "href",
    "/backtests/7"
  );
  expect(fetchMock.mock.calls.filter(([url]) => url === "/api/dashboard")).toHaveLength(1);
});

it.each([
  ["/", "Dashboard", /Dashboard loaded/],
  ["/signals", "Signals", /#42/],
  ["/backtests", "Backtests", /#8/],
  ["/etfs/1", "ETF Detail", /NYSEARCA:SPY/],
  ["/signals/42", "Signal Detail", /Signal #42/],
  ["/backtests/8", "Backtest Detail", /Backtest #8/]
])("renders exactly one page-level h1 on %s", async (route, headingName, successText) => {
  window.history.pushState({}, "", route);
  vi.stubGlobal("fetch", vi.fn().mockImplementation((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/dashboard") {
      return Promise.resolve(jsonResponse(createDashboardResponse()));
    }

    if (url === "/api/strategy-signals?limit=20&offset=0") {
      return Promise.resolve(
        jsonResponse({
          signals: [
            {
              signal_id: 42,
              signal_date: "2026-06-23",
              config_version: "v1",
              status: "success",
              result: "rebalance",
              generated_at: "2026-06-23T09:30:00",
              is_fallback: false,
              position_count: 2
            }
          ]
        })
      );
    }

    if (url === "/api/backtests?limit=10&offset=0") {
      return Promise.resolve(
        jsonResponse({
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
        })
      );
    }

    if (url === "/api/etfs/1/prices?range=1y") {
      return Promise.resolve(jsonResponse(createEtfPriceTrendResponse()));
    }

    if (url === "/api/strategy-signals/42") {
      return Promise.resolve(jsonResponse(createSignalDetailResponse()));
    }

    if (url === "/api/backtests/8") {
      return Promise.resolve(jsonResponse(createBacktestDetailResponse()));
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  }));

  render(<App />);

  expect(await screen.findByText(successText)).toBeInTheDocument();
  expect(screen.getByRole("heading", { level: 1, name: headingName })).toBeInTheDocument();
  expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  expect(screen.queryByRole("heading", { name: "Vela Research" })).not.toBeInTheDocument();
});

it("renders signal detail data fetched by id", async () => {
  window.history.pushState({}, "", "/signals/42");
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/strategy-signals/42") {
      return Promise.resolve(jsonResponse(createSignalDetailResponse()));
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(screen.getByRole("heading", { name: "Signal Detail" })).toBeInTheDocument();
  expect(await screen.findByText("Signal #42")).toBeInTheDocument();
  expect(screen.getByText("2026-06-23")).toBeInTheDocument();
  expect(screen.getByText("dual_momentum")).toBeInTheDocument();
  expect(screen.getByText("v1")).toBeInTheDocument();
  expect(screen.getByText("rebalance")).toBeInTheDocument();
  expect(screen.getAllByText("No")).toHaveLength(2);
  expect(screen.getByText("2026-06-23T09:30:00")).toBeInTheDocument();
  const holdingsTable = screen.getByRole("table");
  const holdings = within(holdingsTable);
  expect(holdings.getAllByRole("row")).toHaveLength(3);
  expect(screen.getByRole("heading", { name: "Target holdings" })).toBeInTheDocument();
  expect(holdings.getByRole("columnheader", { name: "Exchange" })).toBeInTheDocument();
  expect(holdings.getByRole("columnheader", { name: "Symbol" })).toBeInTheDocument();
  expect(holdings.getByRole("columnheader", { name: "Target weight" })).toBeInTheDocument();
  expect(holdings.getByRole("columnheader", { name: "Rank" })).toBeInTheDocument();
  expect(holdings.getByRole("columnheader", { name: "Score" })).toBeInTheDocument();
  expect(holdings.getByRole("columnheader", { name: "Fallback" })).toBeInTheDocument();
  expect(holdings.getByText("SSE")).toBeInTheDocument();
  expect(holdings.getByText("510300")).toBeInTheDocument();
  expect(holdings.getByText("33.3333%")).toBeInTheDocument();
  expect(holdings.getByText("1")).toBeInTheDocument();
  expect(holdings.getByText("0.812345")).toBeInTheDocument();
  expect(holdings.getByText("SZSE")).toBeInTheDocument();
  expect(holdings.getByText("159915")).toBeInTheDocument();
  expect(holdings.getByText("100%")).toBeInTheDocument();
  expect(holdings.getAllByText("n/a")).toHaveLength(2);
  expect(holdings.getByText("Yes")).toBeInTheDocument();
  expect(screen.queryByText(/candidate/i)).not.toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith("/api/strategy-signals/42", undefined);
});

it("renders shared page loading feedback on the signal detail route", () => {
  window.history.pushState({}, "", "/signals/42");
  const signalDetailResult = createDeferred<Response>();
  vi.stubGlobal("fetch", vi.fn().mockReturnValue(signalDetailResult.promise));

  render(<App />);

  expect(screen.getByRole("status", { name: "" })).toHaveTextContent("Loading signal detail.");
  expect(screen.queryByText("Signal #42")).not.toBeInTheDocument();
});

it("renders an empty target holdings state on the signal detail route", async () => {
  window.history.pushState({}, "", "/signals/42");
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      jsonResponse({
        ...createSignalDetailResponse(),
        positions: []
      })
    )
  );

  render(<App />);

  expect(await screen.findByText("Signal #42")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Target holdings" })).toBeInTheDocument();
  expect(screen.getByText("No target holdings were stored for this signal.")).toBeInTheDocument();
  expect(screen.queryByText(/Signal detail API unavailable/i)).not.toBeInTheDocument();
});

it("shows loading instead of stale signal detail when the route id changes", async () => {
  window.history.pushState({}, "", "/signals/42");
  const nextSignalResult = createDeferred<Response>();
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/strategy-signals/42") {
      return Promise.resolve(jsonResponse(createSignalDetailResponse()));
    }

    if (url === "/api/strategy-signals/43") {
      return nextSignalResult.promise;
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(await screen.findByText("Signal #42")).toBeInTheDocument();
  window.history.pushState({}, "", "/signals/43");
  fireEvent.popState(window);

  expect(await screen.findByText("Loading signal detail.")).toBeInTheDocument();
  expect(screen.queryByText("Signal #42")).not.toBeInTheDocument();

  nextSignalResult.resolve(
    jsonResponse({
      ...createSignalDetailResponse(),
      signal: {
        ...createSignalDetailResponse().signal,
        signal_id: 43,
        signal_date: "2026-06-24"
      }
    })
  );

  expect(await screen.findByText("Signal #43")).toBeInTheDocument();
  expect(screen.getByText("2026-06-24")).toBeInTheDocument();
});

it("renders a not-found state on the signal detail route when the id is unknown", async () => {
  window.history.pushState({}, "", "/signals/999");
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(jsonResponse({ detail: "Strategy signal not found" }, 404))
  );

  render(<App />);

  expect(await screen.findByText("Signal 999 was not found.")).toBeInTheDocument();
  expect(screen.queryByText(/Signal detail API unavailable/i)).not.toBeInTheDocument();
});

it("renders an API failure state on the signal detail route", async () => {
  window.history.pushState({}, "", "/signals/42");
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));

  render(<App />);

  expect(await screen.findByText("Signal detail API unavailable: network")).toBeInTheDocument();
});

it("loads backtest detail data through the shared client", async () => {
  window.history.pushState({}, "", "/backtests/8");
  const fetchMock = vi.fn().mockResolvedValue(jsonResponse(createBacktestDetailResponse()));
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(screen.getByRole("heading", { name: "Backtest Detail" })).toBeInTheDocument();
  expect(await screen.findByText("Backtest #8")).toBeInTheDocument();
  expect(screen.getByText("dual_momentum")).toBeInTheDocument();
  expect(screen.getByText("v1")).toBeInTheDocument();
  expect(screen.getByText("2026-01-01 to 2026-01-31")).toBeInTheDocument();
  expect(screen.getByText("success")).toBeInTheDocument();
  expect(screen.getByText("2026-02-01T09:00:00")).toBeInTheDocument();
  expect(screen.getByText("2026-02-01T09:05:00")).toBeInTheDocument();
  expect(screen.getByText("12.00%")).toBeInTheDocument();
  expect(screen.getByText("144.00%")).toBeInTheDocument();
  expect(screen.getByText("-5.00%")).toBeInTheDocument();
  expect(screen.getByText("20.00%")).toBeInTheDocument();
  expect(screen.getByText("1.10")).toBeInTheDocument();
  const metricsSection = screen.getByRole("heading", { name: "Metrics" }).closest("section");
  expect(metricsSection).not.toBeNull();
  const metrics = within(metricsSection as HTMLElement);
  expect(metrics.getByText("Total return")).toBeInTheDocument();
  expect(metrics.getByText("12.00%")).toBeInTheDocument();
  expect(metrics.getByText("Annualized return")).toBeInTheDocument();
  expect(metrics.getByText("144.00%")).toBeInTheDocument();
  expect(metrics.getByText("Max drawdown")).toBeInTheDocument();
  expect(metrics.getByText("-5.00%")).toBeInTheDocument();
  expect(metrics.getByText("Volatility")).toBeInTheDocument();
  expect(metrics.getByText("20.00%")).toBeInTheDocument();
  expect(metrics.getByText("Sharpe ratio")).toBeInTheDocument();
  expect(metrics.getByText("1.10")).toBeInTheDocument();
  const equitySection = screen.getByRole("heading", { name: "Equity curve" }).closest("section");
  expect(equitySection).not.toBeNull();
  const equityCurve = within(equitySection as HTMLElement);
  expect(equityCurve.getByRole("img", { name: "Equity curve net value chart" })).toBeInTheDocument();
  expect(equityCurve.getByTestId("equity-curve-line")).toHaveClass("equity-curve-line");
  const highlights = equityCurve.getAllByTestId("equity-curve-highlight");
  expect(highlights).toHaveLength(2);
  for (const highlight of highlights) {
    expect(highlight).toHaveClass("equity-curve-highlight");
    expect(highlight).toHaveAttribute("r", "4");
  }
  expect(equityCurve.getByText("Point count")).toBeInTheDocument();
  expect(equityCurve.getByText("2")).toBeInTheDocument();
  expect(equityCurve.getByText("Start point")).toBeInTheDocument();
  expect(equityCurve.getByText("2026-01-02 / 1.0100")).toBeInTheDocument();
  expect(equityCurve.getByText("End point")).toBeInTheDocument();
  expect(equityCurve.getByText("2026-01-05 / 1.0300")).toBeInTheDocument();
  expect(equityCurve.getByText("1.0100")).toBeInTheDocument();
  expect(equityCurve.getByText("1.0300")).toBeInTheDocument();
  expect(screen.getByText(/"top_n": 2/)).toBeInTheDocument();
  expect(screen.queryByText(/drawdown curve|monthly returns|return distribution/i)).not.toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith("/api/backtests/8", undefined);
});

it("renders an empty equity curve state on the backtest detail route", async () => {
  window.history.pushState({}, "", "/backtests/8");
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      jsonResponse({
        ...createBacktestDetailResponse(),
        equity_curve: []
      })
    )
  );

  render(<App />);

  const equitySection = (await screen.findByRole("heading", { name: "Equity curve" })).closest(
    "section"
  );
  expect(equitySection).not.toBeNull();
  const equityCurve = within(equitySection as HTMLElement);
  expect(equityCurve.getByText("No valid equity curve points are available for this run.")).toBeInTheDocument();
  expect(equityCurve.queryByTestId("equity-curve-line")).not.toBeInTheDocument();
  expect(equityCurve.queryAllByTestId("equity-curve-highlight")).toHaveLength(0);
  expect(screen.queryByText(/Backtest detail API unavailable/i)).not.toBeInTheDocument();
});

it("renders a single-point equity curve state on the backtest detail route", async () => {
  window.history.pushState({}, "", "/backtests/8");
  const detail = createBacktestDetailResponse();
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      jsonResponse({
        ...detail,
        equity_curve: detail.equity_curve.slice(0, 1)
      })
    )
  );

  render(<App />);

  const equitySection = (await screen.findByRole("heading", { name: "Equity curve" })).closest(
    "section"
  );
  expect(equitySection).not.toBeNull();
  const equityCurve = within(equitySection as HTMLElement);
  expect(equityCurve.getByText("Only one equity curve point is available.")).toBeInTheDocument();
  expect(equityCurve.getByText("Point count")).toBeInTheDocument();
  expect(equityCurve.getByText("1")).toBeInTheDocument();
  expect(equityCurve.getByText("2026-01-02")).toBeInTheDocument();
  expect(equityCurve.getByText("1.0100")).toBeInTheDocument();
  expect(equityCurve.queryByTestId("equity-curve-line")).not.toBeInTheDocument();
  expect(equityCurve.queryAllByTestId("equity-curve-highlight")).toHaveLength(0);
  expect(screen.queryByText(/Backtest detail API unavailable/i)).not.toBeInTheDocument();
});

it("renders n/a for nullable backtest metric cards", async () => {
  window.history.pushState({}, "", "/backtests/8");
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      jsonResponse({
        ...createBacktestDetailResponse(),
        metrics: {
          total_return: null,
          annualized_return: null,
          max_drawdown: null,
          volatility: null,
          sharpe_ratio: null
        }
      })
    )
  );

  render(<App />);

  const metricsSection = (await screen.findByRole("heading", { name: "Metrics" })).closest(
    "section"
  );
  expect(metricsSection).not.toBeNull();
  expect(within(metricsSection as HTMLElement).getAllByText("n/a")).toHaveLength(5);
  expect(screen.getByText("Backtest #8")).toBeInTheDocument();
  expect(screen.queryByText(/Backtest detail API unavailable/i)).not.toBeInTheDocument();
});

it("renders a loading state on the backtest detail route", () => {
  window.history.pushState({}, "", "/backtests/8");
  const deferred = createDeferred<Response>();
  vi.stubGlobal("fetch", vi.fn().mockReturnValue(deferred.promise));

  render(<App />);

  expect(screen.getByText("Loading backtest detail.")).toBeInTheDocument();
  expect(screen.getByRole("status", { name: "" })).toHaveTextContent("Loading backtest detail.");
  expect(screen.queryByText("Backtest #8")).not.toBeInTheDocument();
});

it("renders a missing state on the backtest detail route", async () => {
  window.history.pushState({}, "", "/backtests/999");
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(jsonResponse({ detail: "Backtest run not found" }, 404))
  );

  render(<App />);

  expect(await screen.findByText("Backtest run 999 was not found.")).toBeInTheDocument();
  expect(screen.queryByText(/Backtest detail API unavailable/i)).not.toBeInTheDocument();
});

it("renders an API failure state on the backtest detail route", async () => {
  window.history.pushState({}, "", "/backtests/8");
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));

  render(<App />);

  expect(await screen.findByText("Backtest detail API unavailable: network")).toBeInTheDocument();
});

it("renders backtest list rows on the /backtests route", async () => {
  window.history.pushState({}, "", "/backtests");
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/backtests?limit=10&offset=0") {
      return Promise.resolve(
        jsonResponse({
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
        })
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(screen.getByRole("heading", { name: "Backtests" })).toBeInTheDocument();
  expect(await screen.findByRole("link", { name: "#8" })).toHaveAttribute("href", "/backtests/8");
  expect(screen.getByText("2026-01-01 to 2026-01-31")).toBeInTheDocument();
  expect(screen.getByText("success")).toBeInTheDocument();
  expect(screen.getByText("2026-02-01T09:00:00")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith("/api/backtests?limit=10&offset=0", undefined);
});

it("shows loading instead of stale backtest rows when pagination changes", async () => {
  window.history.pushState({}, "", "/backtests");
  const nextPageResult = createDeferred<Response>();
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/backtests?limit=10&offset=0") {
      return Promise.resolve(
        jsonResponse({
          runs: Array.from({ length: 10 }, (_, index) => ({
            run_id: index + 1,
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
          }))
        })
      );
    }

    if (url === "/api/backtests?limit=10&offset=10") {
      return nextPageResult.promise;
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(await screen.findByRole("link", { name: "#1" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Next" }));

  expect(screen.getByText("Loading backtest history.")).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: "#1" })).not.toBeInTheDocument();

  nextPageResult.resolve(
    jsonResponse({
      runs: [
        {
          run_id: 11,
          strategy_id: "dual_momentum",
          config_version: "v1",
          start_date: "2026-02-01",
          end_date: "2026-02-28",
          status: "success",
          started_at: "2026-03-01T09:00:00",
          finished_at: "2026-03-01T09:05:00",
          total_return: "0.130000",
          annualized_return: "1.560000",
          max_drawdown: "-0.040000",
          volatility: "0.210000",
          sharpe_ratio: "1.200000"
        }
      ]
    })
  );

  expect(await screen.findByRole("link", { name: "#11" })).toBeInTheDocument();
  expect(screen.getByText("2026-02-01 to 2026-02-28")).toBeInTheDocument();
});

it("shows an empty state on /backtests when no backtest runs exist", async () => {
  window.history.pushState({}, "", "/backtests");
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/backtests?limit=10&offset=0") {
      return Promise.resolve(jsonResponse({ runs: [] }));
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(
    await screen.findByText(
      "No local backtest run exists yet. Run a backtest from the Dashboard to see its detail here."
    )
  ).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith("/api/backtests?limit=10&offset=0", undefined);
});

it("shows an error state on /backtests when the backtests list API fails", async () => {
  window.history.pushState({}, "", "/backtests");
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));

  render(<App />);

  expect(await screen.findByText("Backtest history API unavailable: network")).toBeInTheDocument();
});

it("shows an error state on /backtests when the backtests list API returns a server error", async () => {
  window.history.pushState({}, "", "/backtests");
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/backtests?limit=10&offset=0") {
      return Promise.resolve(
        new Response(JSON.stringify({ detail: "Internal error" }), {
          headers: { "Content-Type": "application/json" },
          status: 500
        })
      );
    }

    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(await screen.findByText("Backtest history API unavailable: http")).toBeInTheDocument();
});

it("renders an etf-row entry control linking to the ETF price trend page", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(createDashboardResponse())));

  render(<App />);

  await screen.findByText("1,200 rows");
  expect(screen.getByRole("link", { name: "View SPY price trend" })).toHaveAttribute(
    "href",
    "/etfs/1"
  );
  expect(screen.getByRole("link", { name: "View QQQ price trend" })).toHaveAttribute(
    "href",
    "/etfs/2"
  );
});

it("omits the etf-row entry control when etf_id is absent", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      jsonResponse({
        ...createDashboardResponse(),
        market_data: {
          ...createDashboardResponse().market_data,
          etf_list: [
            { exchange: "NYSEARCA", symbol: "SPY", name: "SPY ETF", category: "equity_us" }
          ]
        }
      })
    )
  );

  render(<App />);

  await screen.findByText("1,200 rows");
  expect(screen.queryByRole("link", { name: /price trend/i })).not.toBeInTheDocument();
});

it("renders the ETF price trend chart with a multi-point series", async () => {
  window.history.pushState({}, "", "/etfs/1");
  const fetchMock = vi.fn().mockResolvedValue(jsonResponse(createEtfPriceTrendResponse()));
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(screen.getByRole("heading", { name: "ETF Detail" })).toBeInTheDocument();
  expect(await screen.findByText("NYSEARCA:SPY")).toBeInTheDocument();
  expect(screen.getByText("SPY ETF")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "1Y" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByTestId("trend-line")).toBeInTheDocument();
  expect(screen.getByTestId("trend-highlight")).toBeInTheDocument();
  const readout = screen.getByTestId("trend-readout");
  expect(readout).toHaveTextContent("2026-03-02");
  expect(readout).toHaveTextContent("101.25");
  expect(fetchMock).toHaveBeenCalledWith("/api/etfs/1/prices?range=1y", undefined);
});

const trendOverlayRect = {
  x: 0,
  y: 0,
  width: 640,
  height: 260,
  top: 0,
  left: 0,
  bottom: 260,
  right: 640,
  toJSON: () => ({})
} as DOMRect;

it("resolves the nearest trend point from the pointer x-coordinate", () => {
  // 3 points on a 568-wide drawable area: x(0)=56, x(1)=340, x(2)=624 (spacing 284).
  expect(indexFromX(56, 3)).toBe(0);
  expect(indexFromX(340, 3)).toBe(1);
  expect(indexFromX(624, 3)).toBe(2);
});

it("clamps the trend hover index to the series bounds", () => {
  expect(indexFromX(-100, 3)).toBe(0);
  expect(indexFromX(9999, 3)).toBe(2);
});

it("resolves the nearest trend point at band boundaries without half-cell offset", () => {
  // Cursor at 220 falls inside the old band-0 cell [56, 245.33] but is nearer to point 1
  // (x=340, dist 120) than point 0 (x=56, dist 164). Point-grid round resolves to 1, not
  // band cell 0 -- the half-cell misalignment is gone. The switch happens at midpoint 198.
  expect(indexFromX(197, 3)).toBe(0);
  expect(indexFromX(199, 3)).toBe(1);
  expect(indexFromX(220, 3)).toBe(1);
});

it("updates the trend readout and highlight to the hovered price point", async () => {
  window.history.pushState({}, "", "/etfs/1");
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(createEtfPriceTrendResponse())));

  render(<App />);

  const readout = await screen.findByTestId("trend-readout");
  expect(readout).toHaveTextContent("2026-03-02");

  const overlay = screen.getByTestId("trend-hover-overlay");
  vi.spyOn(overlay, "getBoundingClientRect").mockReturnValue(trendOverlayRect);

  fireEvent.mouseMove(overlay, { clientX: 56 });
  expect(readout).toHaveTextContent("2026-01-02");
  expect(readout).toHaveTextContent("100");
  expect(screen.getByTestId("trend-highlight")).toHaveAttribute("cx", "56");

  fireEvent.mouseMove(overlay, { clientX: 340 });
  expect(readout).toHaveTextContent("2026-02-02");
  expect(screen.getByTestId("trend-highlight")).toHaveAttribute("cx", "340");
});

it("serves trend hover hit detection from a single overlay element", async () => {
  window.history.pushState({}, "", "/etfs/1");
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(createEtfPriceTrendResponse())));

  render(<App />);

  await screen.findByTestId("trend-line");
  expect(screen.getAllByTestId("trend-hover-overlay")).toHaveLength(1);
  expect(screen.queryByTestId("trend-hover-band")).not.toBeInTheDocument();
});

it("reverts the trend readout to the latest point when the pointer leaves", async () => {
  window.history.pushState({}, "", "/etfs/1");
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(createEtfPriceTrendResponse())));

  render(<App />);

  const overlay = await screen.findByTestId("trend-hover-overlay");
  vi.spyOn(overlay, "getBoundingClientRect").mockReturnValue(trendOverlayRect);
  const readout = screen.getByTestId("trend-readout");

  fireEvent.mouseMove(overlay, { clientX: 56 });
  expect(readout).toHaveTextContent("2026-01-02");

  fireEvent.mouseLeave(screen.getByRole("img", { name: "ETF backward-adjusted price trend" }));
  expect(readout).toHaveTextContent("2026-03-02");
});

it("renders a single-point trend state with its readout", async () => {
  window.history.pushState({}, "", "/etfs/1");
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      jsonResponse({
        ...createEtfPriceTrendResponse(),
        points: [{ trade_date: "2026-01-02", price: "100.0000" }]
      })
    )
  );

  render(<App />);

  expect(await screen.findByText("Only one price point is available.")).toBeInTheDocument();
  expect(screen.getByText("2026-01-02")).toBeInTheDocument();
  expect(screen.getByText("100")).toBeInTheDocument();
  expect(screen.queryByTestId("trend-line")).not.toBeInTheDocument();
});

it("renders an empty trend state when no price points exist", async () => {
  window.history.pushState({}, "", "/etfs/1");
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(jsonResponse({ ...createEtfPriceTrendResponse(), points: [] }))
  );

  render(<App />);

  expect(
    await screen.findByText("No price data is available for this ETF and horizon.")
  ).toBeInTheDocument();
  expect(screen.queryByTestId("trend-line")).not.toBeInTheDocument();
});

it("refetches the trend when the horizon changes", async () => {
  window.history.pushState({}, "", "/etfs/1");
  const nextRangeResult = createDeferred<Response>();
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/etfs/1/prices?range=1y") {
      return Promise.resolve(jsonResponse(createEtfPriceTrendResponse()));
    }
    if (url === "/api/etfs/1/prices?range=3m") {
      return nextRangeResult.promise;
    }
    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  await screen.findByText("NYSEARCA:SPY");
  expect(fetchMock).toHaveBeenCalledWith("/api/etfs/1/prices?range=1y", undefined);
  fireEvent.click(screen.getByRole("button", { name: "3M" }));
  expect(screen.getByText("Loading ETF price trend.")).toBeInTheDocument();
  expect(screen.queryByText("NYSEARCA:SPY")).not.toBeInTheDocument();

  nextRangeResult.resolve(jsonResponse(createEtfPriceTrendResponse()));

  await screen.findByText("NYSEARCA:SPY");
  expect(fetchMock).toHaveBeenCalledWith("/api/etfs/1/prices?range=3m", undefined);
  expect(screen.getByRole("button", { name: "3M" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("button", { name: "1Y" })).toHaveAttribute("aria-pressed", "false");
});

it("renders a loading state on the ETF detail route", () => {
  window.history.pushState({}, "", "/etfs/1");
  const deferred = createDeferred<Response>();
  vi.stubGlobal("fetch", vi.fn().mockReturnValue(deferred.promise));

  render(<App />);

  expect(screen.getByText("Loading ETF price trend.")).toBeInTheDocument();
  expect(screen.queryByTestId("trend-line")).not.toBeInTheDocument();
});

it("renders a not-found state on the ETF detail route when the id is unknown", async () => {
  window.history.pushState({}, "", "/etfs/999");
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(jsonResponse({ detail: "ETF not found" }, 404))
  );

  render(<App />);

  expect(await screen.findByText("ETF 999 was not found.")).toBeInTheDocument();
  expect(screen.queryByText(/ETF trend API unavailable/i)).not.toBeInTheDocument();
});

it("renders an API failure state on the ETF detail route", async () => {
  window.history.pushState({}, "", "/etfs/1");
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));

  render(<App />);

  expect(await screen.findByText("ETF trend API unavailable: network")).toBeInTheDocument();
});

it("exposes local research navigation without production account entry points", () => {
  render(<App />);

  expect(screen.getByRole("link", { name: "Dashboard" })).toHaveAttribute("href", "/");
  expect(screen.getByRole("link", { name: "Signals" })).toHaveAttribute("href", "/signals");
  expect(screen.getByRole("link", { name: "Backtests" })).toHaveAttribute("href", "/backtests");

  expect(screen.queryByText(/login|sign up|account|team|deploy|production/i)).not.toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /latest signal/i })).not.toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /backtest detail/i })).not.toBeInTheDocument();
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
        assets: [
          {
            exchange: "SSE",
            symbol: "511010"
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
        { etf_id: 1, exchange: "NYSEARCA", symbol: "SPY", name: "SPY ETF", category: "equity_us" },
        { etf_id: 2, exchange: "NYSEARCA", symbol: "QQQ", name: "QQQ ETF", category: "equity_us_tech" },
      ],
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
      },
      {
        fetch_log_id: 10,
        fetch_time: "2026-06-23T07:05:00",
        mode: "full",
        status: "success",
        rows_fetched: 200,
        rows_inserted: 180,
        rows_updated: 20,
        error_summary: null
      }
    ]
  };
}

function createSignalDetailResponse() {
  return {
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
        target_weight: "0.333333",
        rank: 1,
        score: "0.812345",
        is_fallback: false
      },
      {
        exchange: "SZSE",
        symbol: "159915",
        target_weight: "1.000000",
        rank: null,
        score: null,
        is_fallback: true
      }
    ]
  };
}

function createGeneratedLatestSignalResponse() {
  return {
    has_signal: true,
    signal: {
      signal_id: 43,
      signal_date: "2026-06-24",
      config_version: "v1",
      result: "rebalance",
      generated_at: "2026-06-24T09:30:00",
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
      },
      {
        exchange: "SZSE",
        symbol: "159915",
        target_weight: "0.500000",
        rank: 2,
        score: "0.700000",
        is_fallback: false
      }
    ]
  };
}

function createBacktestRunResponse() {
  return {
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
}

function createBacktestDetailResponse() {
  return {
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
      },
      {
        trade_date: "2026-01-05",
        net_value: "1.030000",
        cash: "100.000000",
        market_value: "10100.000000",
        total_assets: "10200.000000",
        positions_json: "[{\"symbol\": \"510300\", \"weight\": 1.0}]"
      }
    ]
  };
}

function createEtfPriceTrendResponse() {
  return {
    etf: { id: 1, exchange: "NYSEARCA", symbol: "SPY", name: "SPY ETF" },
    points: [
      { trade_date: "2026-01-02", price: "100.0000" },
      { trade_date: "2026-02-02", price: "102.5000" },
      { trade_date: "2026-03-02", price: "101.2500" }
    ]
  };
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    status
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
