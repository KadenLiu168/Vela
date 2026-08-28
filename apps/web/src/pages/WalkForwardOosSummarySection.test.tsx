import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import type {
  WalkForwardBenchmarkEvidence,
  WalkForwardBenchmarkKey,
  WalkForwardEvidence,
  WalkForwardEvidenceStatus,
  WalkForwardMetricSummary,
  WalkForwardRateSummary
} from "../api/client";
import { WalkForwardOosSummarySection } from "./WalkForwardOosSummarySection";

function metric(
  value: number | null,
  status: WalkForwardEvidenceStatus = "sufficient"
): WalkForwardMetricSummary {
  return {
    mean: value,
    median: value,
    min: value,
    max: value,
    std: 0.01,
    window_count: 2,
    valid_count: value === null ? 0 : 2,
    evidence_status: status
  };
}

function rate(value: number | null, numerator: number, denominator: number): WalkForwardRateSummary {
  return {
    numerator,
    denominator,
    value,
    window_count: 2,
    valid_count: 2,
    evidence_status: "sufficient"
  };
}

function benchmarkEvidence(): WalkForwardBenchmarkEvidence {
  return {
    total_return_difference: metric(0.01),
    annualized_return_difference: metric(0.02),
    tracking_error: metric(0.04),
    information_ratio: metric(0.6),
    outperformance_rate: rate(0.5, 1, 2)
  };
}

function makeEvidence(overrides?: Partial<WalkForwardEvidence>): WalkForwardEvidence {
  return {
    metrics: {
      total_return: { ...metric(0.0234), mean: 0.0312 },
      annualized_return: metric(0.08),
      sharpe_ratio: metric(1.1),
      max_drawdown: metric(-0.15),
      volatility: metric(0.15),
      sortino_ratio: metric(1.4),
      calmar_ratio: metric(0.5),
      longest_drawdown_duration_sessions: metric(8)
    },
    positive_window_rate: rate(0.75, 3, 4),
    generalization_gap: metric(0.03),
    benchmarks: {
      equal_weight_monthly: benchmarkEvidence(),
      csi_300_buy_hold: benchmarkEvidence()
    },
    parameter_stability: {
      lookback_days: {
        value_frequencies: { "120": 2 },
        transition_count: 1,
        comparison_count: 4,
        transition_rate: 0.25
      }
    },
    ...overrides
  };
}

it("renders the six headline cards from persisted cross-window evidence fields", () => {
  render(<WalkForwardOosSummarySection evidence={makeEvidence()} status="success" />);

  expect(screen.getByRole("heading", { name: "OOS summary" })).toBeInTheDocument();
  expect(screen.getByLabelText("OOS summary headline metrics").tagName).toBe("DL");
  // Median return as primary with mean as secondary and the window annotation.
  expect(screen.getByText("2.34%")).toBeInTheDocument();
  expect(screen.getByText("mean 3.12%")).toBeInTheDocument();
  expect(screen.getByText("median across 2 windows")).toBeInTheDocument();
  // Ratio metrics keep ratio format without a percent sign.
  expect(screen.getByText("1.10")).toBeInTheDocument();
  // Max drawdown renders as a percentage.
  expect(screen.getByText("-15.00%")).toBeInTheDocument();
  // Rate metrics carry their fraction context.
  expect(screen.getByText("75.00%")).toBeInTheDocument();
  expect(screen.getByText("3/4 windows")).toBeInTheDocument();
  // Outperformance against the primary benchmark with its name and fraction.
  expect(screen.getByText("50.00%")).toBeInTheDocument();
  expect(screen.getByText(/vs CSI 300 buy-and-hold · 1\/2 windows/)).toBeInTheDocument();
  // Transition max with parameter name and comparison context.
  expect(screen.getByText("25.00%")).toBeInTheDocument();
  expect(screen.getByText(/lookback_days · 4 comparisons/)).toBeInTheDocument();
  // No synthesized verdict language.
  expect(screen.queryByText(/score|pass|fail/i)).not.toBeInTheDocument();
});

it("presents the Generalization Gap and Evidence Status as explained facts", () => {
  render(<WalkForwardOosSummarySection evidence={makeEvidence()} status="success" />);

  expect(
    screen.getByText(/Generalization gap \(IS Sharpe − OOS Sharpe\): median 0\.03/)
  ).toBeInTheDocument();
  expect(
    screen.getByText(/a positive gap means in-sample selection performed better than out-of-sample/)
  ).toBeInTheDocument();
  expect(
    screen.getByText(/the larger the gap, the weaker the generalization/)
  ).toBeInTheDocument();
  expect(
    screen.getByText(/Evidence status: sufficient — sufficient requires at least three valid windows/)
  ).toBeInTheDocument();
});

it("uses the persisted total-return evidence status even when insufficient", () => {
  render(
    <WalkForwardOosSummarySection
      evidence={makeEvidence({ metrics: { ...makeEvidence().metrics, total_return: metric(0.01, "insufficient_evidence") } })}
      status="success"
    />
  );

  expect(
    screen.getByText(/Evidence status: insufficient_evidence — sufficient requires at least three valid windows/)
  ).toBeInTheDocument();
});

it("falls back to the first benchmark when the CSI-300 key is absent", () => {
  render(
    <WalkForwardOosSummarySection
      evidence={makeEvidence({
        benchmarks: {
          equal_weight_monthly: benchmarkEvidence()
        } as Record<WalkForwardBenchmarkKey, WalkForwardBenchmarkEvidence>
      })}
      status="success"
    />
  );

  expect(screen.getByText(/vs Equal-weight monthly · 1\/2 windows/)).toBeInTheDocument();
});

it("renders outperformance as unavailable without benchmark evidence", () => {
  render(
    <WalkForwardOosSummarySection
      evidence={makeEvidence({
        benchmarks: {} as Record<WalkForwardBenchmarkKey, WalkForwardBenchmarkEvidence>
      })}
      status="success"
    />
  );

  expect(screen.getByText("n/a")).toBeInTheDocument();
  expect(screen.queryByText(/vs /)).not.toBeInTheDocument();
});

it("shows the maximum per-parameter transition with its comparison context", () => {
  render(
    <WalkForwardOosSummarySection
      evidence={makeEvidence({
        parameter_stability: {
          first_param: {
            value_frequencies: { "1": 1 },
            transition_count: 1,
            comparison_count: 4,
            transition_rate: 0.25
          },
          second_param: {
            value_frequencies: { "1": 1 },
            transition_count: 5,
            comparison_count: 9,
            transition_rate: 0.6
          }
        }
      })}
      status="success"
    />
  );

  expect(screen.getByText("60.00%")).toBeInTheDocument();
  expect(screen.getByText(/second_param · 9 comparisons/)).toBeInTheDocument();
  expect(screen.queryByText(/first_param · /)).not.toBeInTheDocument();
});

it("keeps the pre-terminal note for queued and running runs without fabricating values", () => {
  const { rerender } = render(
    <WalkForwardOosSummarySection evidence={null} status="queued" />
  );

  expect(
    screen.getByText("Evidence is unavailable until this queued run reaches a terminal state.")
  ).toBeInTheDocument();
  expect(screen.queryByText("OOS total return")).not.toBeInTheDocument();
  expect(screen.queryByText("75.00%")).not.toBeInTheDocument();

  rerender(<WalkForwardOosSummarySection evidence={null} status="running" />);
  expect(
    screen.getByText("Evidence is unavailable until this running run reaches a terminal state.")
  ).toBeInTheDocument();
});

it("states why evidence is unavailable for a failed run", () => {
  render(<WalkForwardOosSummarySection evidence={null} status="failed" />);

  expect(screen.getByText("Evidence is unavailable because this run failed.")).toBeInTheDocument();
  expect(screen.queryByText("OOS total return")).not.toBeInTheDocument();
});

it("renders null metric values as n/a instead of fabricating numbers", () => {
  render(
    <WalkForwardOosSummarySection
      evidence={makeEvidence({
        metrics: { ...makeEvidence().metrics, max_drawdown: metric(null) }
      })}
      status="success"
    />
  );

  expect(screen.getByText("n/a")).toBeInTheDocument();
  expect(screen.queryByText("NaN")).not.toBeInTheDocument();
});
