import { describe, expect, it } from "vitest";
import type {
  WalkForwardBenchmarkEvidence,
  WalkForwardBenchmarkKey,
  WalkForwardMetricSummary
} from "../api/client";
import {
  aggregateTransitionRate,
  formatPercentNumber,
  generalizationGapText,
  resolvePrimaryBenchmark
} from "./walkForwardFormatters";

function metric(value: number | null = 0.1): WalkForwardMetricSummary {
  return {
    mean: value,
    median: value,
    min: value,
    max: value,
    std: 0.01,
    window_count: 2,
    valid_count: value === null ? 0 : 2,
    evidence_status: "sufficient"
  };
}

function benchmarkEvidence(): WalkForwardBenchmarkEvidence {
  return {
    total_return_difference: metric(0.01),
    annualized_return_difference: metric(0.02),
    tracking_error: metric(0.04),
    information_ratio: metric(0.6),
    outperformance_rate: {
      numerator: 1,
      denominator: 2,
      value: 0.5,
      window_count: 2,
      valid_count: 2,
      evidence_status: "sufficient"
    }
  };
}

describe("formatPercentNumber", () => {
  it("renders stored ratios as percentages with two digits by default", () => {
    expect(formatPercentNumber(0.0234)).toBe("2.34%");
    expect(formatPercentNumber(-0.2)).toBe("-20.00%");
  });

  it("honours the requested digit count", () => {
    expect(formatPercentNumber(0.0234, 1)).toBe("2.3%");
    expect(formatPercentNumber(1, 0)).toBe("100%");
  });

  it("renders zero and null without fabricating a value", () => {
    expect(formatPercentNumber(0)).toBe("0.00%");
    expect(formatPercentNumber(null)).toBe("n/a");
  });
});

describe("resolvePrimaryBenchmark", () => {
  it("prefers csi_300_buy_hold even when another benchmark is inserted first", () => {
    const primary = resolvePrimaryBenchmark({
      equal_weight_monthly: benchmarkEvidence(),
      csi_300_buy_hold: benchmarkEvidence()
    });
    expect(primary?.key).toBe("csi_300_buy_hold");
  });

  it("falls back to the first benchmark in the collection when the CSI-300 key is absent", () => {
    const primary = resolvePrimaryBenchmark({
      equal_weight_monthly: benchmarkEvidence()
    } as Record<WalkForwardBenchmarkKey, WalkForwardBenchmarkEvidence>);
    expect(primary?.key).toBe("equal_weight_monthly");
    expect(primary?.benchmark).toBeDefined();
  });

  it("returns null when no benchmark evidence exists", () => {
    expect(
      resolvePrimaryBenchmark({} as Record<WalkForwardBenchmarkKey, WalkForwardBenchmarkEvidence>)
    ).toBeNull();
  });
});

describe("aggregateTransitionRate", () => {
  const stability = (transitionRate: number | null, comparisonCount: number) => ({
    value_frequencies: { "120": 1 },
    transition_count: 0,
    comparison_count: comparisonCount,
    transition_rate: transitionRate
  });

  it("picks the maximum per-parameter transition rate with its comparison context", () => {
    const aggregate = aggregateTransitionRate({
      lookback_days: stability(0, 1),
      top_n: stability(0.5, 8)
    });
    expect(aggregate).toEqual({ rate: 0.5, parameterName: "top_n", comparisonCount: 8 });
  });

  it("carries a low comparison base so the headline cannot be misread", () => {
    const aggregate = aggregateTransitionRate({
      lookback_days: stability(1, 1)
    });
    expect(aggregate).toEqual({ rate: 1, parameterName: "lookback_days", comparisonCount: 1 });
  });

  it("keeps the first parameter in insertion order on tied maximum rates", () => {
    const aggregate = aggregateTransitionRate({
      first_param: stability(0.5, 4),
      second_param: stability(0.5, 4)
    });
    expect(aggregate?.parameterName).toBe("first_param");
  });

  it("skips null transition rates and returns null when no parameter has comparisons", () => {
    expect(
      aggregateTransitionRate({
        no_comparisons: stability(null, 0),
        also_no_comparisons: stability(null, 0)
      })
    ).toBeNull();
    expect(aggregateTransitionRate({})).toBeNull();
  });
});

describe("generalizationGapText", () => {
  it("presents the median as a ratio with the IS-minus-OOS-Sharpe meaning and direction", () => {
    const text = generalizationGapText(metric(0.03));
    expect(text).toContain("Generalization gap (IS Sharpe − OOS Sharpe): median 0.03");
    expect(text).toContain("a positive gap means in-sample selection performed better than out-of-sample");
    expect(text).toContain("the larger the gap, the weaker the generalization");
    expect(text).not.toContain("%");
  });

  it("renders an unavailable median without fabricating a value", () => {
    expect(generalizationGapText(metric(null))).toContain("median n/a");
  });
});
