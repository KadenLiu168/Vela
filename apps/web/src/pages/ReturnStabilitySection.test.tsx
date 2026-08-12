import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ReturnStability } from "../api/client";
import { ReturnStabilitySection } from "./ReturnStabilitySection";

const stabilityFixture = (): ReturnStability => ({
  strategy: {
    window_sessions: 63,
    rolling_status: "available",
    sharpe_status: "available",
    source_point_count: 66,
    effective_return_count: 65,
    rolling: [
      {
        window_start_date: "2026-01-01",
        trade_date: "2026-03-31",
        total_return: "0.123456",
        volatility: "0.182345",
        sharpe_ratio: "0.871234"
      },
      {
        window_start_date: "2026-01-02",
        trade_date: "2026-04-01",
        total_return: "0.130000",
        volatility: "0.190000",
        sharpe_ratio: "0.900000"
      }
    ],
    monthly: [
      {
        period: "2026-01",
        first_date: "2026-01-02",
        last_date: "2026-01-30",
        observation_count: 21,
        total_return: "0.030000",
        is_partial: false
      },
      {
        period: "2026-02",
        first_date: "2026-02-02",
        last_date: "2026-02-27",
        observation_count: 20,
        total_return: "-0.010000",
        is_partial: false
      }
    ],
    yearly: [
      {
        period: "2026",
        first_date: "2026-01-02",
        last_date: "2026-04-01",
        observation_count: 65,
        total_return: "0.130000",
        is_partial: true
      }
    ]
  },
  benchmarks: [
    {
      key: "equal_weight_monthly",
      name: "Equal-weight monthly rebalanced portfolio",
      window_sessions: 63,
      rolling_status: "available",
      sharpe_status: "available",
      source_point_count: 66,
      effective_return_count: 65,
      rolling: [
        {
          window_start_date: "2026-01-01",
          trade_date: "2026-03-31",
          total_return: "0.090000",
          volatility: "0.150000",
          sharpe_ratio: "0.700000"
        }
      ],
      monthly: [
        {
          period: "2026-01",
          first_date: "2026-01-02",
          last_date: "2026-01-30",
          observation_count: 21,
          total_return: "0.020000",
          is_partial: false
        }
      ],
      yearly: []
    }
  ]
});

function renderSection(stability: ReturnStability = stabilityFixture()) {
  return render(<ReturnStabilitySection stability={stability} />);
}

describe("ReturnStabilitySection", () => {
  it("labels the 63-session window and explains backend derivation", () => {
    renderSection();

    expect(screen.getByRole("heading", { name: "Return stability" })).toBeInTheDocument();
    expect(screen.getByText(/63-session trailing window/)).toBeInTheDocument();
    expect(screen.getByText(/computed by the backend/)).toBeInTheDocument();
  });

  it("selects among rolling metrics without recomputation", () => {
    renderSection();

    const selector = screen.getByRole("group", { name: "Rolling metric selector" });
    expect(within(selector).getByRole("button", { name: "Rolling Return" })).toHaveAttribute(
      "aria-pressed",
      "true"
    );

    fireEvent.click(within(selector).getByRole("button", { name: "Rolling Volatility" }));
    expect(
      within(selector).getByRole("button", { name: "Rolling Volatility" })
    ).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByTitle("Rolling Volatility comparison chart")).toBeInTheDocument();

    fireEvent.click(within(selector).getByRole("button", { name: "Rolling Sharpe" }));
    expect(screen.getByTitle("Rolling Sharpe comparison chart")).toBeInTheDocument();
  });

  it("keeps strategy and benchmark identities distinct", () => {
    renderSection();

    const legend = screen.getByRole("list", { name: "Rolling Return legend" });
    expect(legend).toHaveTextContent("Strategy");
    expect(legend).toHaveTextContent("Equal-weight monthly rebalanced portfolio");
    expect(screen.getByTestId("rolling-line-return-strategy")).toBeInTheDocument();
    expect(
      screen.getByTestId("rolling-line-return-equal_weight_monthly")
    ).toBeInTheDocument();
  });

  it("shows exact API values in the accessible table", () => {
    renderSection();
    const selector = screen.getByRole("group", { name: "Rolling metric selector" });

    expect(screen.getByText("0.123456")).toBeInTheDocument();
    expect(screen.getAllByText("0.130000").length).toBeGreaterThan(0);
    expect(screen.getAllByText("2026-01-01").length).toBeGreaterThan(0);
    expect(screen.getAllByText("2026-03-31").length).toBeGreaterThan(0);

    // Switch to Volatility to surface its exact API values.
    fireEvent.click(within(selector).getByRole("button", { name: "Rolling Volatility" }));
    expect(screen.getByText("0.182345")).toBeInTheDocument();

    // Switch to Sharpe to surface its exact API values.
    fireEvent.click(within(selector).getByRole("button", { name: "Rolling Sharpe" }));
    expect(screen.getByText("0.871234")).toBeInTheDocument();
    expect(screen.getAllByText("0.900000").length).toBeGreaterThan(0);
  });

  it("renders monthly and yearly tables with partial markers", () => {
    renderSection();

    expect(screen.getByText("2026-01")).toBeInTheDocument();
    expect(screen.getByText("2026-02")).toBeInTheDocument();
    expect(screen.getByText("0.030000")).toBeInTheDocument();
    expect(screen.getByText("-0.010000")).toBeInTheDocument();
    expect(screen.getAllByText("complete").length).toBeGreaterThan(0);
    // The yearly bucket is partial because requested bounds do not cover the year.
    expect(screen.getByText("partial")).toBeInTheDocument();
    expect(
      screen.getAllByText(/does not certify that every official session/)
    ).not.toHaveLength(0);
  });

  it("switches calendar entity via the selector", () => {
    renderSection();

    const entitySelect = screen.getByLabelText("Entity");
    fireEvent.change(entitySelect, { target: { value: "equal_weight_monthly" } });
    expect(screen.getByText("0.020000")).toBeInTheDocument();
  });

  it("explains insufficient observations without hiding calendar returns", () => {
    const stability = stabilityFixture();
    stability.strategy.rolling_status = "insufficient_observations";
    stability.strategy.rolling = [];
    stability.benchmarks = [];
    renderSection(stability);

    expect(screen.getByText(/Fewer than 64 persisted points/)).toBeInTheDocument();
    expect(screen.getByText("0.030000")).toBeInTheDocument();
  });

  it("explains missing risk-free-rate Sharpe unavailability", () => {
    const stability = stabilityFixture();
    stability.strategy.sharpe_status = "unavailable_missing_risk_free_rate";
    stability.strategy.rolling = stability.strategy.rolling.map((point) => ({
      ...point,
      sharpe_ratio: null
    }));
    stability.benchmarks = [];
    renderSection(stability);

    expect(screen.getByText(/lacks? a risk-free rate/)).toBeInTheDocument();
    expect(screen.getByText("0.123456")).toBeInTheDocument();
  });

  it("renders an empty state when the strategy curve is empty", () => {
    renderSection(emptyStability());

    expect(screen.getByText(/Fewer than 64 persisted points/)).toBeInTheDocument();
    expect(screen.getByText(/No calendar-period returns/)).toBeInTheDocument();
  });

  it("assigns explicit key colors to rolling lines, swatches, and end-labels", () => {
    renderSection();

    expect(screen.getByTestId("rolling-line-return-strategy")).toHaveAttribute("stroke", "var(--color-series-1)");
    expect(screen.getByTestId("rolling-line-return-equal_weight_monthly")).toHaveAttribute("stroke", "var(--color-series-2)");

    const legend = screen.getByRole("list", { name: "Rolling Return legend" });
    expect(within(legend).getByTestId("equity-curve-swatch-strategy")).toHaveStyle({ backgroundColor: "var(--color-series-1)" });
    expect(within(legend).getByTestId("equity-curve-swatch-equal_weight_monthly")).toHaveStyle({ backgroundColor: "var(--color-series-2)" });

    expect(screen.getByTestId("rolling-end-label-return-strategy")).toHaveAttribute("fill", "var(--color-series-1)");
    expect(screen.getByTestId("rolling-end-label-return-equal_weight_monthly")).toHaveAttribute("fill", "var(--color-series-2)");
  });

  it("renders date x-axis ticks and metric-correct y-axis ticks", () => {
    renderSection();

    const xTickValues = screen.getAllByTestId("rolling-x-tick").map((tick) => tick.textContent);
    expect(xTickValues).toContain("2026-03-31");
    expect(xTickValues).toContain("2026-04-01");

    // Return ticks are percentages spanning [9%, 13%] (0.09..0.13).
    const returnYTicks = screen.getAllByTestId("rolling-y-tick").map((tick) => tick.textContent);
    expect(returnYTicks).toContain("12%");
    expect(returnYTicks).toContain("9%");

    // Volatility ticks are percentages spanning [15%, 19%] (0.15..0.19).
    fireEvent.click(screen.getByRole("button", { name: "Rolling Volatility" }));
    const volatilityYTicks = screen.getAllByTestId("rolling-y-tick").map((tick) => tick.textContent);
    expect(volatilityYTicks).toContain("18%");

    // Sharpe ticks are ratios spanning [0.7, 0.9].
    fireEvent.click(screen.getByRole("button", { name: "Rolling Sharpe" }));
    const sharpeYTicks = screen.getAllByTestId("rolling-y-tick").map((tick) => tick.textContent);
    expect(sharpeYTicks).toContain("0.9");
  });

  it("keeps the exact-value table available next to the chart", () => {
    renderSection();

    expect(screen.getByText("0.123456")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Exact Rolling Return values by window" })).toBeInTheDocument();
  });
});

function emptyStability(): ReturnStability {
  return {
    strategy: {
      window_sessions: 63,
      rolling_status: "insufficient_observations",
      sharpe_status: "insufficient_observations",
      source_point_count: 0,
      effective_return_count: 0,
      rolling: [],
      monthly: [],
      yearly: []
    },
    benchmarks: []
  };
}
