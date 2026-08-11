import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { DashboardResponse, MarketDataFetchResponse } from "../api/client";
import { DashboardPage } from "./DashboardPage";

function RouterWrapper({ children }: { children: ReactNode }) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

const dashboardFixture = (): DashboardResponse => ({
  strategy: {
    strategy_id: "equal-weight-test",
    version: "v1",
    universe_config: "etf_cn_11",
    costs: { transaction_cost_bps: 10 },
    performance: {},
    rebalance: { frequency: "monthly" },
    type: "equal_weight",
    parameters: {}
  },
  market_data: {
    price_rows: 100,
    covered_etfs: 5,
    earliest_trade_date: "2026-01-01",
    latest_trade_date: "2026-07-01",
    etf_list: [
      {
        etf_id: 1,
        exchange: "SSE",
        symbol: "510300",
        name: "沪深300ETF",
        category: "equity_cn",
        earliest_trade_date: "2026-01-01"
      }
    ]
  },
  latest_signal: null,
  recent_backtest: null,
  recent_fetch_logs: []
});

const fetchResultFixture = (): MarketDataFetchResponse => ({
  status: "success",
  requested_etf_count: 5,
  rows_fetched: 100,
  rows_inserted: 60,
  rows_updated: 40,
  failed_symbols: [],
  error_message: null
});

const jsonResponse = (body: unknown, status = 200): Response =>
  new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    status
  });

const createFetchMock = ({ postResponse }: { postResponse?: Promise<Response> } = {}) =>
  vi.fn((input: RequestInfo | URL): Promise<Response> => {
    const url = typeof input === "string" ? input : String(input);
    if (url === "/api/dashboard") {
      return Promise.resolve(jsonResponse(dashboardFixture()));
    }
    if (url === "/api/market-data/fetch?mode=full" || url === "/api/market-data/fetch?mode=incremental") {
      return postResponse ?? Promise.resolve(jsonResponse(fetchResultFixture()));
    }
    return Promise.reject(new Error(`Unexpected fetch: ${url}`));
  });

const postFetchCalls = (fetchMock: ReturnType<typeof vi.fn>) =>
  fetchMock.mock.calls.filter((call) => call[1]?.method === "POST");

describe("DashboardPage market data fetch actions", () => {
  it("issues a full market data fetch when the Fetch full button is clicked", async () => {
    const fetchMock = createFetchMock();
    vi.stubGlobal("fetch", fetchMock);

    render(<DashboardPage />, { wrapper: RouterWrapper });

    fireEvent.click(await screen.findByRole("button", { name: "Fetch full" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/market-data/fetch?mode=full", { method: "POST" });
    });
    expect(fetchMock).not.toHaveBeenCalledWith("/api/market-data/fetch?mode=incremental", { method: "POST" });
  });

  it("keeps the incremental fetch request unchanged when the Fetch market data button is clicked", async () => {
    const fetchMock = createFetchMock();
    vi.stubGlobal("fetch", fetchMock);

    render(<DashboardPage />, { wrapper: RouterWrapper });

    fireEvent.click(await screen.findByRole("button", { name: "Fetch market data" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith("/api/market-data/fetch?mode=incremental", { method: "POST" });
    });
    expect(fetchMock).not.toHaveBeenCalledWith("/api/market-data/fetch?mode=full", { method: "POST" });
  });

  it("disables the sibling fetch button while a fetch is in flight and issues no second request", async () => {
    let resolveFetch!: (response: Response) => void;
    const pendingFetch = new Promise<Response>((resolve) => {
      resolveFetch = resolve;
    });
    const fetchMock = createFetchMock({ postResponse: pendingFetch });
    vi.stubGlobal("fetch", fetchMock);

    render(<DashboardPage />, { wrapper: RouterWrapper });

    fireEvent.click(await screen.findByRole("button", { name: "Fetch full" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Fetching full market data" })).toBeDisabled();
    });
    expect(screen.getByRole("button", { name: "Fetch market data" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Fetch market data" }));
    expect(postFetchCalls(fetchMock)).toHaveLength(1);

    resolveFetch(jsonResponse(fetchResultFixture()));
    await screen.findByRole("button", { name: "Fetch full" });
  });

  it("shows the full fetch in-progress label only while a full fetch is in flight", async () => {
    let resolveFetch!: (response: Response) => void;
    const pendingFetch = new Promise<Response>((resolve) => {
      resolveFetch = resolve;
    });
    const fetchMock = createFetchMock({ postResponse: pendingFetch });
    vi.stubGlobal("fetch", fetchMock);

    render(<DashboardPage />, { wrapper: RouterWrapper });

    fireEvent.click(await screen.findByRole("button", { name: "Fetch full" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Fetching full market data" })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Fetch market data" })).toBeInTheDocument();

    resolveFetch(jsonResponse(fetchResultFixture()));
    await screen.findByRole("button", { name: "Fetch full" });
    expect(screen.queryByRole("button", { name: "Fetching full market data" })).not.toBeInTheDocument();
  });

  it("shows the incremental fetch in-progress label only while an incremental fetch is in flight", async () => {
    let resolveFetch!: (response: Response) => void;
    const pendingFetch = new Promise<Response>((resolve) => {
      resolveFetch = resolve;
    });
    const fetchMock = createFetchMock({ postResponse: pendingFetch });
    vi.stubGlobal("fetch", fetchMock);

    render(<DashboardPage />, { wrapper: RouterWrapper });

    fireEvent.click(await screen.findByRole("button", { name: "Fetch market data" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Fetching market data" })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Fetch full" })).toBeInTheDocument();

    resolveFetch(jsonResponse(fetchResultFixture()));
    await screen.findByRole("button", { name: "Fetch market data" });
    expect(screen.queryByRole("button", { name: "Fetching market data" })).not.toBeInTheDocument();
  });

  it("renders the shared market data fetch summary after a successful full fetch", async () => {
    const fetchMock = createFetchMock();
    vi.stubGlobal("fetch", fetchMock);

    render(<DashboardPage />, { wrapper: RouterWrapper });

    fireEvent.click(await screen.findByRole("button", { name: "Fetch full" }));

    expect(await screen.findByText("Market data fetch success")).toBeInTheDocument();
    expect(screen.getByText("Fetched")).toBeInTheDocument();
    expect(screen.getByText("60 rows")).toBeInTheDocument();
    expect(screen.getByText("Inserted")).toBeInTheDocument();
    expect(screen.getByText("40 rows")).toBeInTheDocument();
    expect(screen.getByText("Updated")).toBeInTheDocument();
  });

  it("renders the operation error summary when a full fetch fails", async () => {
    const fetchMock = createFetchMock({
      postResponse: Promise.resolve(
        jsonResponse(
          {
            error: {
              code: "operation_failed",
              category: "operation_failed",
              message: "Provider timeout"
            }
          },
          500
        )
      )
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<DashboardPage />, { wrapper: RouterWrapper });

    fireEvent.click(await screen.findByRole("button", { name: "Fetch full" }));

    expect(await screen.findByText("Market data fetch failed")).toBeInTheDocument();
    expect(screen.getByText("Provider timeout")).toBeInTheDocument();
  });

  it("disables the full fetch button while an incremental fetch is in flight and issues no second request", async () => {
    let resolveFetch!: (response: Response) => void;
    const pendingFetch = new Promise<Response>((resolve) => {
      resolveFetch = resolve;
    });
    const fetchMock = createFetchMock({ postResponse: pendingFetch });
    vi.stubGlobal("fetch", fetchMock);

    render(<DashboardPage />, { wrapper: RouterWrapper });

    fireEvent.click(await screen.findByRole("button", { name: "Fetch market data" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Fetching market data" })).toBeDisabled();
    });
    expect(screen.getByRole("button", { name: "Fetch full" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Fetch full" }));
    expect(postFetchCalls(fetchMock)).toHaveLength(1);

    resolveFetch(jsonResponse(fetchResultFixture()));
    await screen.findByRole("button", { name: "Fetch market data" });
  });

  it("reloads aggregate dashboard data after a successful full fetch", async () => {
    let dashboardCallCount = 0;
    const fetchMock = vi.fn((input: RequestInfo | URL): Promise<Response> => {
      const url = typeof input === "string" ? input : String(input);
      if (url === "/api/dashboard") {
        dashboardCallCount += 1;
        const priceRows = dashboardCallCount === 1 ? 100 : 250;
        return Promise.resolve(
          jsonResponse({
            ...dashboardFixture(),
            market_data: { ...dashboardFixture().market_data, price_rows: priceRows }
          })
        );
      }
      if (url === "/api/market-data/fetch?mode=full") {
        return Promise.resolve(jsonResponse(fetchResultFixture()));
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<DashboardPage />, { wrapper: RouterWrapper });

    expect(await screen.findByText("100 rows")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Fetch full" }));

    await waitFor(() => {
      expect(screen.getByText("250 rows")).toBeInTheDocument();
    });
    expect(dashboardCallCount).toBe(2);
  });
});
