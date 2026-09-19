import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { DashboardResponse } from "../api/client";
import { ResearchStatusSection } from "./ResearchStatusSection";

function dashboard(overrides: Partial<DashboardResponse> = {}): DashboardResponse {
  return {
    strategy: {
      strategy_id: "Dual_momentum",
      version: "v1",
      universe_config: "config/etf_pool.yaml",
      costs: { transaction_cost_bps: 10 },
      performance: {},
      rebalance: { frequency: "weekly" },
      type: "equal_weight",
      parameters: {}
    },
    market_data: {
      price_rows: 29498,
      covered_etfs: 11,
      earliest_trade_date: "2011-12-09",
      latest_trade_date: "2026-08-07",
      etf_list: []
    },
    latest_signal: null,
    recent_backtest: null,
    latest_walk_forward: null,
    recent_fetch_logs: [],
    ...overrides
  };
}

const staleSignal = {
  signal_id: 307,
  signal_date: "2024-12-31",
  config_version: "v1",
  status: "success",
  result: "rebalance",
  generated_at: "2026-08-12T03:11:57",
  is_fallback: false,
  position_count: 2,
  source: "manual",
  backtest_run_id: null,
  positions: []
};

describe("ResearchStatusSection", () => {
  it("renders the four current-state facts", () => {
    render(
      <ResearchStatusSection
        data={dashboard({ latest_signal: staleSignal })}
      />
    );

    const region = screen.getByRole("region", { name: "Current research state" });
    expect(within(region).getByText("Market data")).toBeInTheDocument();
    expect(within(region).getByText("Latest signal")).toBeInTheDocument();
    expect(within(region).getByText("Latest backtest")).toBeInTheDocument();
    expect(within(region).getByText("Walk-forward")).toBeInTheDocument();
    expect(within(region).getByText("Stored through 2026-08-07")).toBeInTheDocument();
    expect(within(region).getByText("Signalled for 2024-12-31")).toBeInTheDocument();
  });

  it("states the lag in calendar days with both dates visible", () => {
    render(<ResearchStatusSection data={dashboard({ latest_signal: staleSignal })} />);

    expect(
      screen.getByText("584 calendar days behind the stored market data")
    ).toBeInTheDocument();
    expect(screen.getByText("Signalled for 2024-12-31")).toBeInTheDocument();
    expect(screen.getByText("Stored through 2026-08-07")).toBeInTheDocument();
  });

  it("does not describe a current signal as lagging", () => {
    render(
      <ResearchStatusSection
        data={dashboard({ latest_signal: { ...staleSignal, signal_date: "2026-08-07" } })}
      />
    );

    expect(screen.queryByText(/calendar days behind the stored market data/)).not.toBeInTheDocument();
  });

  it("states missing artifacts instead of placeholders", () => {
    render(<ResearchStatusSection data={dashboard()} />);

    expect(screen.getByText("No successful signal")).toBeInTheDocument();
    expect(screen.getByText("No backtest run")).toBeInTheDocument();
    expect(screen.getByText("No run yet")).toBeInTheDocument();
  });

  it("offers one next action that targets the pre-existing control", () => {
    render(<ResearchStatusSection data={dashboard()} />);

    const action = screen.getByRole("link", { name: "Generate signal" });
    expect(action).toHaveAttribute("href", "#dashboard-generate-signal");
  });

  it("prefers the market-data action when no price rows are stored", () => {
    render(
      <ResearchStatusSection
        data={dashboard({
          market_data: {
            price_rows: 0,
            covered_etfs: 0,
            earliest_trade_date: null,
            latest_trade_date: null,
            etf_list: []
          }
        })}
      />
    );

    expect(screen.getByRole("link", { name: "Fetch market data" })).toHaveAttribute(
      "href",
      "#dashboard-fetch-market-data"
    );
  });

  it("offers no corrective action once everything is current", () => {
    render(
      <ResearchStatusSection
        data={dashboard({
          latest_signal: { ...staleSignal, signal_date: "2026-08-07" },
          recent_backtest: {
            run_id: 1,
            strategy_id: "Dual_momentum",
            config_version: "v1",
            start_date: "2019-01-01",
            end_date: "2026-08-07",
            status: "success",
            total_return: "-0.17",
            annualized_return: "-0.03",
            max_drawdown: "-0.41",
            sharpe_ratio: "-0.15",
            started_at: "2026-08-12T03:11:57",
            benchmarks: []
          }
        })}
      />
    );

    expect(
      screen.getByText("Market data and the latest signal are current; no corrective action is needed.")
    ).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Generate signal|Fetch market data|Run a backtest/ })).not.toBeInTheDocument();
  });

  it("does not claim a lagging backtest range is current when no action is offered", () => {
    render(
      <ResearchStatusSection
        data={dashboard({
          latest_signal: { ...staleSignal, signal_date: "2026-08-07" },
          recent_backtest: {
            run_id: 1,
            strategy_id: "Dual_momentum",
            config_version: "v1",
            start_date: "2019-01-01",
            end_date: "2024-12-31",
            status: "success",
            total_return: "-0.17",
            annualized_return: "-0.03",
            max_drawdown: "-0.41",
            sharpe_ratio: "-0.15",
            started_at: "2026-08-12T03:11:57",
            benchmarks: []
          }
        })}
      />
    );

    expect(screen.getByText("584 calendar days behind the stored market data")).toBeInTheDocument();
    expect(screen.queryByText(/backtest .*current|current .*backtest/)).not.toBeInTheDocument();
  });

  it("renders no acid-lime primary fill", () => {
    const { container } = render(<ResearchStatusSection data={dashboard()} />);

    expect(container.querySelectorAll(".button-primary")).toHaveLength(0);
  });
});
