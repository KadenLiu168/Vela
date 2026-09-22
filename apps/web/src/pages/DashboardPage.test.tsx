import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  latest_walk_forward: null,
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

describe("DashboardPage decision-first research path", () => {
  const populatedFixture = (): DashboardResponse => ({
    ...dashboardFixture(),
    latest_signal: {
      signal_id: 307,
      signal_date: "2024-12-31",
      config_version: "v1",
      status: "success",
      result: "rebalance",
      generated_at: "2026-08-12T03:11:57",
      is_fallback: false,
      position_count: 2,
      source: "backtest",
      backtest_run_id: 1,
      positions: [
        {
          exchange: "SSE",
          symbol: "588000",
          name: "科创50ETF",
          target_weight: "0.500000",
          rank: 1,
          score: "0.409997",
          is_fallback: false
        },
        {
          exchange: "SZSE",
          symbol: "159915",
          name: "创业板ETF",
          target_weight: "0.500000",
          rank: 2,
          score: "0.253804",
          is_fallback: false
        }
      ]
    },
    recent_backtest: {
      run_id: 1,
      strategy_id: "Dual_momentum",
      config_version: "v1",
      start_date: "2019-01-01",
      end_date: "2024-12-31",
      status: "success",
      total_return: "-0.173422",
      annualized_return: "-0.031245",
      max_drawdown: "-0.418520",
      sharpe_ratio: "-0.154367",
      started_at: "2026-08-12T03:11:57",
      benchmarks: [
        {
          key: "csi_300_buy_hold",
          name: "CSI 300 buy-and-hold",
          total_return: "0.427400",
          total_return_difference: "-0.600822",
          annualized_return_difference: "-0.092348",
          sharpe_ratio: "0.322564",
          max_drawdown: "-0.384516"
        }
      ]
    },
    latest_walk_forward: {
      run_id: 1,
      strategy_id: "Dual_momentum",
      status: "queued",
      start_date: "2019-01-01",
      end_date: "2024-12-31",
      window_count: 0,
      finished_at: null,
      error_message: null,
      oos: null
    }
  });

  const renderPopulated = async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL): Promise<Response> => {
        const url = typeof input === "string" ? input : String(input);
        if (url === "/api/dashboard") {
          return Promise.resolve(jsonResponse(populatedFixture()));
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      })
    );

    render(<DashboardPage />, { wrapper: RouterWrapper });
    await screen.findByText("Current state");
  };

  it("renders the five decision layers ahead of the reference region", async () => {
    await renderPopulated();

    const page = screen.getByRole("heading", { name: "Dashboard" }).closest("section") as HTMLElement;
    const decisionPath = page.querySelector(".research-decision-path") as HTMLElement;
    const referenceGrid = page.querySelector(".dashboard-grid") as HTMLElement;

    expect(decisionPath.compareDocumentPosition(referenceGrid)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING
    );
    const headings = Array.from(
      decisionPath.querySelectorAll(".panel-heading h3")
    ).map((node) => node.textContent);
    expect(headings).toEqual([
      "Current state",
      "Latest result",
      "Latest result",
      "OOS evidence",
      "Drill down"
    ]);
  });

  it("renders the latest signal target holdings in the decision path", async () => {
    await renderPopulated();

    const holdings = screen.getByRole("table", { name: "Latest signal target holdings" });
    expect(within(holdings).getByText("588000")).toBeInTheDocument();
    expect(within(holdings).getByText("科创50ETF")).toBeInTheDocument();
    const cells = within(within(holdings).getAllByRole("row")[1]).getAllByRole("cell");
    expect(cells[0]).toHaveClass("mono-compact");
    expect(cells[1]).not.toHaveClass("mono-compact");
    expect(cells[2]).toHaveClass("mono-compact");
    expect(cells[3]).toHaveClass("mono-compact");
    expect(cells[4]).toHaveClass("mono-compact");
  });

  it("states that a backtest-sourced signal is a simulation, not a live instruction", async () => {
    await renderPopulated();

    const signalPanel = screen.getByTestId("workflow-panel-signal");
    expect(within(signalPanel).getByText("Source")).toBeInTheDocument();
    expect(within(signalPanel).getByText("Backtest")).toBeInTheDocument();
    expect(
      within(signalPanel).getByText(/these holdings are simulated positions, not a current instruction/)
    ).toBeInTheDocument();
    expect(
      within(signalPanel).getByRole("link", { name: "backtest #1" })
    ).toHaveAttribute("href", "/backtests/1");
  });

  it("contrasts the latest backtest with its primary benchmark", async () => {
    await renderPopulated();

    expect(screen.getByText("vs CSI 300 buy-and-hold: -60.08%")).toBeInTheDocument();
    expect(screen.getByText("vs CSI 300 buy-and-hold: deeper by 3.40%")).toBeInTheDocument();
  });

  it("states which config version produced the shown performance", async () => {
    await renderPopulated();

    const backtestPanel = screen.getByTestId("workflow-panel-backtest");
    expect(within(backtestPanel).getByText("Config version")).toBeInTheDocument();
    expect(within(backtestPanel).getByText("v1")).toHaveClass("mono-compact");
  });

  it("reports the latest walk-forward state without scoring it", async () => {
    await renderPopulated();

    expect(screen.getByText("Walk-forward #1")).toBeInTheDocument();
    expect(
      screen.getByText("Evidence is unavailable until this queued run reaches a terminal state.")
    ).toBeInTheDocument();
  });

  it("indexes the existing research routes from the deep-evidence layer", async () => {
    await renderPopulated();

    expect(screen.getByRole("link", { name: "Signal history" })).toHaveAttribute("href", "/signals");
    expect(screen.getByRole("link", { name: "Backtest history" })).toHaveAttribute(
      "href",
      "/backtests"
    );
    expect(
      screen.getByRole("link", { name: "Walk-forward history and stitched OOS evidence" })
    ).toHaveAttribute("href", "/walk-forwards");
  });
});
