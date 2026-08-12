import { render, screen, within } from "@testing-library/react";
import { expect, it } from "vitest";
import type { BacktestBenchmark, BacktestDetailMetrics } from "../api/client";
import { DecisionSummarySection } from "./DecisionSummarySection";

const metrics: BacktestDetailMetrics = {
  total_return: "0.12",
  annualized_return: "0.11",
  max_drawdown: "-0.09",
  volatility: "0.15",
  sharpe_ratio: "1.5",
  sortino_ratio: null,
  calmar_ratio: null,
  longest_drawdown_duration_sessions: null,
  longest_drawdown_peak_date: null,
  longest_drawdown_trough_date: null,
  longest_drawdown_recovery_date: null,
  historical_var_95: null,
  historical_cvar_95: null,
  return_skewness: null,
  return_excess_kurtosis: null,
  distribution_observation_count: null,
  tail_observation_count: null,
  distribution_evidence_status: "unavailable_legacy"
};

const benchmark = (overrides: Partial<BacktestBenchmark> = {}): BacktestBenchmark => ({
  key: "csi_300_buy_hold",
  name: "CSI 300 buy-and-hold",
  total_return: "0.08",
  annualized_return: "0.08",
  max_drawdown: "-0.08",
  volatility: "0.2",
  sharpe_ratio: "0.8",
  sortino_ratio: null,
  calmar_ratio: null,
  longest_drawdown_duration_sessions: null,
  longest_drawdown_peak_date: null,
  longest_drawdown_trough_date: null,
  longest_drawdown_recovery_date: null,
  total_return_difference: "0.04",
  annualized_return_difference: "0.03",
  tracking_error: null,
  information_ratio: null,
  capm_alpha: null,
  capm_beta: null,
  capm_r_squared: null,
  capm_observation_count: null,
  up_capture_ratio: null,
  up_capture_observation_count: null,
  down_capture_ratio: null,
  down_capture_observation_count: null,
  equity_curve: [],
  historical_var_95: null,
  historical_cvar_95: null,
  return_skewness: null,
  return_excess_kurtosis: null,
  distribution_observation_count: null,
  tail_observation_count: null,
  distribution_evidence_status: "unavailable_legacy",
  ...overrides
});

const equalWeight = benchmark({
  key: "equal_weight_monthly",
  name: "Equal-weight monthly rebalanced portfolio",
  total_return_difference: "0.02",
  annualized_return_difference: "0.01"
});

function renderSection(benchmarks: BacktestBenchmark[]) {
  return render(<DecisionSummarySection benchmarks={benchmarks} metrics={metrics} />);
}

function decisionMetrics() {
  return within(screen.getByLabelText("Strategy decision summary metrics"));
}

it("shows the four strategy headline values with differences against the primary benchmark", () => {
  renderSection([benchmark()]);

  expect(
    decisionMetrics()
      .getAllByRole("term")
      .map((term) => term.textContent)
  ).toEqual([
    "Total return",
    "CAGR (calendar-time)",
    "Sharpe (daily returns, 252D)",
    "Max drawdown"
  ]);
  expect(decisionMetrics().getByText("12.00%")).toBeInTheDocument();
  expect(decisionMetrics().getByText("11.00%")).toBeInTheDocument();
  expect(decisionMetrics().getByText("1.50")).toBeInTheDocument();
  expect(decisionMetrics().getByText("-9.00%")).toBeInTheDocument();

  // CAGR and Total return differences come from the API difference fields;
  // Sharpe and Max drawdown differences come from display subtraction.
  expect(
    decisionMetrics().getByText("vs CSI 300 buy-and-hold: +4.00%")
  ).toBeInTheDocument();
  expect(
    decisionMetrics().getByText("vs CSI 300 buy-and-hold: +3.00%")
  ).toBeInTheDocument();
  expect(
    decisionMetrics().getByText("vs CSI 300 buy-and-hold: +0.70")
  ).toBeInTheDocument();
  expect(
    decisionMetrics().getByText("vs CSI 300 buy-and-hold: deeper by 1.00%")
  ).toBeInTheDocument();
});

it("prefers the csi_300_buy_hold benchmark as primary when present", () => {
  renderSection([equalWeight, benchmark()]);

  expect(
    screen.getByText(/Primary benchmark: CSI 300 buy-and-hold\./)
  ).toBeInTheDocument();
  expect(decisionMetrics().getByText(/vs CSI 300 buy-and-hold: \+4\.00%/)).toBeInTheDocument();
  expect(screen.queryByText(/vs Equal-weight monthly rebalanced portfolio/)).not.toBeInTheDocument();
});

it("falls back to the first benchmark when csi_300_buy_hold is absent", () => {
  renderSection([equalWeight]);

  expect(
    screen.getByText(/Primary benchmark: Equal-weight monthly rebalanced portfolio\./)
  ).toBeInTheDocument();
  expect(decisionMetrics().getByText(/vs Equal-weight monthly rebalanced portfolio: \+2\.00%/)).toBeInTheDocument();
  expect(decisionMetrics().getByText(/vs Equal-weight monthly rebalanced portfolio: \+1\.00%/)).toBeInTheDocument();
});

it("keeps the four strategy values visible without difference evidence when no benchmarks exist", () => {
  renderSection([]);

  expect(decisionMetrics().getByText("12.00%")).toBeInTheDocument();
  expect(decisionMetrics().getByText("-9.00%")).toBeInTheDocument();
  expect(decisionMetrics().queryByText(/vs /)).not.toBeInTheDocument();
  expect(document.querySelector(".verdict-badge")).toBeNull();
});

it("renders the Outperforming verdict when every valid difference is favorable", () => {
  renderSection([
    benchmark({
      max_drawdown: "-0.10"
    })
  ]);

  expect(screen.getByText("Outperforming")).toBeInTheDocument();
});

it("renders the Underperforming verdict when every valid difference is unfavorable", () => {
  renderSection([
    benchmark({
      total_return_difference: "-0.04",
      annualized_return_difference: "-0.03",
      sharpe_ratio: "1.6",
      max_drawdown: "-0.07"
    })
  ]);

  expect(screen.getByText("Underperforming")).toBeInTheDocument();
});

it("renders the Mixed verdict for a positive/negative sign mix", () => {
  renderSection([benchmark()]);

  expect(screen.getByText("Mixed")).toBeInTheDocument();
});

it("withholds the verdict badge with fewer than two valid differences", () => {
  const sparseMetrics: BacktestDetailMetrics = {
    ...metrics,
    sharpe_ratio: null,
    max_drawdown: null
  };
  render(
    <DecisionSummarySection
      benchmarks={[benchmark({ annualized_return_difference: null })]}
      metrics={sparseMetrics}
    />
  );

  expect(document.querySelector(".verdict-badge")).toBeNull();
  expect(screen.queryByText("Mixed")).not.toBeInTheDocument();
  expect(screen.queryByText("Outperforming")).not.toBeInTheDocument();
  expect(screen.queryByText("Underperforming")).not.toBeInTheDocument();
});

it("frames a shallower max drawdown relative to the primary benchmark", () => {
  renderSection([
    benchmark({
      max_drawdown: "-0.10"
    })
  ]);

  expect(
    decisionMetrics().getByText("vs CSI 300 buy-and-hold: shallower by 1.00%")
  ).toBeInTheDocument();
});
