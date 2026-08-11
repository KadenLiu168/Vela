import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  window.history.pushState({}, "", "/");
  vi.unstubAllGlobals();
});

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    status
  });
}

it("preserves Dashboard backtest form dates across an internal detail transition and return", async () => {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/dashboard") {
      return Promise.resolve(
        jsonResponse({
          strategy: {
            strategy_id: "dual_momentum",
            version: "v1",
            type: "dual_momentum",
            universe_config: "config/etf_pool.yaml",
            parameters: {
              momentum: { long_window_days: 126, short_window_days: 63 },
              score_weights: { momentum: 0.6, quality: 0.4 },
              selection: { top_n: 2 },
              defense: { assets: [] }
            },
            costs: { transaction_cost_bps: 10 },
            performance: { risk_free_rate: 0 },
            rebalance: { frequency: "weekly" }
          },
          market_data: {
            price_rows: 1200,
            covered_etfs: 8,
            earliest_trade_date: "2025-01-02",
            latest_trade_date: "2026-06-23",
            etf_list: []
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
          recent_backtest: null,
          recent_fetch_logs: []
        })
      );
    }
    if (url === "/api/strategy-signals/42") {
      return Promise.resolve(
        jsonResponse({
          signal: {
            signal_id: 42,
            signal_date: "2026-06-23",
            strategy_id: "dual_momentum",
            config_version: "v1",
            generated_at: "2026-06-23T09:30:00",
            result: "rebalance",
            is_fallback: false,
            source: "manual",
            backtest_run_id: null
          },
          positions: []
        })
      );
    }
    if (url === "/api/backtests/run?startDate=2026-01-01&endDate=2026-06-30") {
      return Promise.resolve(jsonResponse({}));
    }
    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  await screen.findByText("1,200 rows");
  fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-01-01" } });
  fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-06-30" } });

  fireEvent.click(screen.getByRole("link", { name: "View signal detail" }));
  expect(await screen.findByRole("heading", { level: 1, name: "Signal Detail" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("link", { name: "Dashboard" }));
  await waitFor(() => {
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  });

  const startInput = screen.getByLabelText("Start date") as HTMLInputElement;
  const endInput = screen.getByLabelText("End date") as HTMLInputElement;
  expect(startInput.value).toBe("2026-01-01");
  expect(endInput.value).toBe("2026-06-30");

  fireEvent.keyDown(window, { key: "k", ctrlKey: true });
  const paletteInput = await screen.findByRole("textbox", { name: "Search" });
  fireEvent.change(paletteInput, { target: { value: "Run backtest" } });
  fireEvent.click(await screen.findByText("Run backtest", { selector: ".command-palette-row-label" }));

  await waitFor(() => {
    expect(fetchMock.mock.calls.some(([input]) => {
      return String(input) === "/api/backtests/run?startDate=2026-01-01&endDate=2026-06-30";
    })).toBe(true);
  });
});
