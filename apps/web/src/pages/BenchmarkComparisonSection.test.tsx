import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it } from "vitest";
import type { BacktestBenchmark, BacktestDetailMetrics } from "../api/client";
import { BenchmarkComparisonSection } from "./BenchmarkComparisonSection";

const metrics: BacktestDetailMetrics = {
  total_return: "0.12",
  annualized_return: "0.11",
  max_drawdown: "-0.09",
  volatility: "0.15",
  sharpe_ratio: "1.5",
  sortino_ratio: "1.8",
  calmar_ratio: "2.1",
  longest_drawdown_duration_sessions: 12,
  longest_drawdown_peak_date: "2026-01-10",
  longest_drawdown_trough_date: "2026-01-20",
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
  key: "equal_weight_monthly",
  name: "Equal-weight monthly rebalanced portfolio",
  total_return: "0.10",
  annualized_return: "0.09",
  max_drawdown: "-0.10",
  volatility: "0.18",
  sharpe_ratio: "1.2",
  sortino_ratio: "1.4",
  calmar_ratio: "1.6",
  longest_drawdown_duration_sessions: 20,
  longest_drawdown_peak_date: "2026-01-11",
  longest_drawdown_trough_date: "2026-01-21",
  longest_drawdown_recovery_date: "2026-01-25",
  tracking_error: "0.038884",
  information_ratio: "12.961481",
  total_return_difference: "0.02",
  annualized_return_difference: "0.02",
  capm_alpha: null,
  capm_beta: null,
  capm_r_squared: null,
  capm_observation_count: null,
  up_capture_ratio: "1.5",
  up_capture_observation_count: 6,
  down_capture_ratio: "0.8",
  down_capture_observation_count: 3,
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

const csi300 = benchmark({
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
  tracking_error: null,
  information_ratio: null,
  total_return_difference: "0.04",
  annualized_return_difference: "0.03",
  up_capture_ratio: "1.3",
  up_capture_observation_count: 5,
  down_capture_ratio: "0.9",
  down_capture_observation_count: 4
});

function renderSection(benchmarks: BacktestBenchmark[], metricOverrides: Partial<BacktestDetailMetrics> = {}) {
  return render(
    <BenchmarkComparisonSection
      benchmarks={benchmarks}
      metrics={{ ...metrics, ...metricOverrides }}
    />
  );
}

function coreTable() {
  return screen.getByRole("table", { name: "Strategy vs benchmark comparison matrix" });
}

function advancedTable() {
  return screen.getByRole("table", { name: "Advanced strategy vs benchmark comparison metrics" });
}

function expandAdvanced() {
  const summary = screen
    .getByRole("heading", { name: "Advanced metrics" })
    .closest("summary");
  fireEvent.click(summary as HTMLElement);
}

it("renders the always-visible core metrics table with one column per entity", () => {
  renderSection([benchmark(), csi300]);

  const table = coreTable();
  expect(
    within(table)
      .getAllByRole("columnheader")
      .map((header) => header.textContent)
  ).toEqual([
    "Metric",
    "Strategy",
    "Equal-weight monthly rebalanced portfolio",
    "CSI 300 buy-and-hold"
  ]);

  for (const label of [
    "Total return",
    "CAGR (calendar-time)",
    "Max drawdown",
    "Annualized volatility (252D)",
    "Sharpe (daily returns, 252D)",
    "Sortino (rf MAR, 252D)",
    "Calmar (calendar CAGR / |MaxDD|)"
  ]) {
    expect(within(table).getByText(label)).toBeInTheDocument();
  }
});

it("keeps Advanced Metrics collapsed by default and reveals the remaining evidence when expanded", () => {
  renderSection([benchmark(), csi300]);

  const advancedHeading = screen.getByRole("heading", { name: "Advanced metrics" });
  const advancedDetails = advancedHeading.closest("details");
  expect(advancedDetails).not.toBeNull();
  expect(advancedDetails).not.toHaveAttribute("open");

  expandAdvanced();
  expect(advancedDetails).toHaveAttribute("open");

  const table = advancedTable();
  for (const label of [
    "Longest drawdown duration (official sessions)",
    "Longest drawdown peak date",
    "Longest drawdown trough date",
    "Longest drawdown recovery",
    "Tracking error (252D)",
    "Information ratio (252D)",
    "Monthly Up Capture (selected months)",
    "Up selected months",
    "Monthly Down Capture (selected months)",
    "Down selected months",
    "Strategy total return difference",
    "Strategy CAGR difference"
  ]) {
    expect(within(table).getByText(label)).toBeInTheDocument();
  }
});

it("marks comparable absolute best cells with visible Best text and never ranks dates or relative rows", () => {
  renderSection([benchmark(), csi300]);
  expandAdvanced();

  const table = coreTable();

  // Total return: strategy 0.12 is highest.
  const totalReturnRow = within(table).getByTestId("comparison-row-total_return");
  expect(within(within(totalReturnRow).getAllByRole("cell")[0]).getByText("Best")).toBeInTheDocument();

  // Max drawdown: CSI 300 -0.08 is closest to zero.
  const maxDrawdownRow = within(table).getByTestId("comparison-row-max_drawdown");
  expect(within(within(maxDrawdownRow).getAllByRole("cell")[2]).getByText("Best")).toBeInTheDocument();

  // Volatility: strategy 0.15 is lowest.
  const volatilityRow = within(table).getByTestId("comparison-row-volatility");
  expect(within(within(volatilityRow).getAllByRole("cell")[0]).getByText("Best")).toBeInTheDocument();

  // Dates and relative rows are never ranked.
  const advanced = advancedTable();
  expect(
    within(within(advanced).getByTestId("comparison-row-longest_drawdown_peak_date")).queryByText("Best")
  ).not.toBeInTheDocument();
  expect(
    within(within(advanced).getByTestId("comparison-row-tracking_error")).queryByText("Best")
  ).not.toBeInTheDocument();
});

it("keeps the strategy cell n/a in strategy-relative rows with capture counts adjacent", () => {
  renderSection([benchmark(), csi300]);
  expandAdvanced();

  const table = advancedTable();
  const trackingRow = within(table).getByTestId("comparison-row-tracking_error");
  const trackingCells = within(trackingRow).getAllByRole("cell");
  expect(trackingCells[0]).toHaveTextContent("n/a");
  expect(trackingCells[1]).toHaveTextContent("0.038884");

  const upCountRow = within(table).getByTestId("comparison-row-up_count");
  expect(within(upCountRow).getByText("6")).toBeInTheDocument();
  expect(within(upCountRow).getByText("5")).toBeInTheDocument();

  const differenceRow = within(table).getByTestId("comparison-row-annualized_return_difference");
  expect(within(differenceRow).getByText("3.00%")).toBeInTheDocument();
});

it("shows the legacy no-benchmark state without fabricating benchmark columns", () => {
  renderSection([]);

  expect(
    screen.getByText("No benchmark comparison is available for this run.")
  ).toBeInTheDocument();
  expect(screen.queryByRole("table", { name: "Strategy vs benchmark comparison matrix" })).not.toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: "Advanced metrics" })).not.toBeInTheDocument();
});

it("renders expanded advanced evidence with ongoing and unavailable values", () => {
  renderSection(
    [
      benchmark({
        key: "equal_weight_monthly",
        name: "Equal-weight monthly rebalanced portfolio",
        total_return: null,
        annualized_return: null,
        max_drawdown: null,
        volatility: null,
        sharpe_ratio: null,
        sortino_ratio: null,
        calmar_ratio: null,
        longest_drawdown_duration_sessions: null,
        longest_drawdown_peak_date: null,
        longest_drawdown_trough_date: null,
        longest_drawdown_recovery_date: null,
        tracking_error: "0.038884",
        information_ratio: "12.961481",
        total_return_difference: null,
        annualized_return_difference: null,
        up_capture_ratio: null,
        up_capture_observation_count: null,
        down_capture_ratio: null,
        down_capture_observation_count: null
      })
    ],
    {
      sortino_ratio: "1.234567",
      calmar_ratio: "2.345678",
      longest_drawdown_duration_sessions: 3,
      longest_drawdown_peak_date: "2026-01-10",
      longest_drawdown_trough_date: "2026-01-20",
      longest_drawdown_recovery_date: null
    }
  );
  expandAdvanced();

  const core = coreTable();
  expect(within(within(core).getByTestId("comparison-row-sortino_ratio")).getByText("1.234567")).toBeInTheDocument();
  expect(within(within(core).getByTestId("comparison-row-calmar_ratio")).getByText("2.345678")).toBeInTheDocument();

  const advanced = advancedTable();
  const durationRow = within(advanced).getByTestId("comparison-row-longest_drawdown_duration_sessions");
  expect(within(durationRow).getByText("3")).toBeInTheDocument();
  expect(within(durationRow).getAllByText("n/a").length).toBe(1);
  expect(
    within(within(advanced).getByTestId("comparison-row-longest_drawdown_peak_date")).getByText("2026-01-10")
  ).toBeInTheDocument();
  expect(
    within(within(advanced).getByTestId("comparison-row-longest_drawdown_trough_date")).getByText("2026-01-20")
  ).toBeInTheDocument();
  expect(
    within(within(advanced).getByTestId("comparison-row-longest_drawdown_recovery")).getByText("ongoing")
  ).toBeInTheDocument();
  expect(
    within(within(advanced).getByTestId("comparison-row-tracking_error")).getByText("0.038884")
  ).toBeInTheDocument();
  expect(
    within(within(advanced).getByTestId("comparison-row-information_ratio")).getByText("12.961481")
  ).toBeInTheDocument();
});

it("renders proxy capture evidence with count units", () => {
  renderSection([
    benchmark({
      up_capture_ratio: "1.995274",
      up_capture_observation_count: 2,
      down_capture_ratio: "0.5",
      down_capture_observation_count: 1
    }),
    {
      ...csi300,
      up_capture_ratio: "1.995274",
      up_capture_observation_count: 2,
      down_capture_ratio: "0.5",
      down_capture_observation_count: 1
    }
  ]);
  expandAdvanced();

  const table = advancedTable();
  expect(within(table).getByText("Monthly Up Capture (selected months)")).toBeInTheDocument();
  expect(within(table).getAllByText("199.53%").length).toBe(2);
  expect(within(table).getByText("Up selected months")).toBeInTheDocument();
  expect(within(table).getByText("Monthly Down Capture (selected months)")).toBeInTheDocument();
  expect(within(table).getAllByText("50.00%").length).toBe(2);
  expect(within(table).getByText("Down selected months")).toBeInTheDocument();
});

it("wraps the core matrix in a labeled keyboard-scrollable region", () => {
  renderSection([benchmark(), csi300]);

  const region = screen.getByLabelText("Strategy vs benchmark comparison matrix region");
  expect(region).toHaveAttribute("tabindex", "0");
  expect(region).toContainElement(coreTable());
});
