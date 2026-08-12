import { describe, expect, it } from "vitest";
import type { BacktestBenchmark } from "../api/client";
import {
  computeMetricDifference,
  computeVerdict,
  formatEquityCurvePoint,
  formatParameterSummary,
  formatParametersHumanReadable,
  parseMetricNumber,
  resolvePrimaryBenchmark
} from "./backtestFormatters";

it("formats parameter summaries without changing null, valid, or malformed JSON behavior", () => {
  expect(formatParameterSummary(null)).toBe("n/a");
  expect(formatParameterSummary('{"top_n":2}')).toBe('{\n  "top_n": 2\n}');
  expect(formatParameterSummary("not-json")).toBe("not-json");
});

it("formats composite equity-curve point readouts", () => {
  expect(formatEquityCurvePoint({ netValue: 1.01, tradeDate: "2026-01-02T00:00:00Z" })).toBe(
    "2026-01-02 / 1.0100"
  );
});

describe("resolvePrimaryBenchmark", () => {
  const benchmark = (key: string): BacktestBenchmark => ({
    key,
    name: key,
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
    total_return_difference: null,
    annualized_return_difference: null,
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
    distribution_evidence_status: "unavailable_legacy"
  });

  it("prefers the csi_300_buy_hold benchmark when present", () => {
    const benchmarks = [benchmark("equal_weight_monthly"), benchmark("csi_300_buy_hold")];
    expect(resolvePrimaryBenchmark(benchmarks)?.key).toBe("csi_300_buy_hold");
  });

  it("falls back to the first benchmark without csi_300_buy_hold", () => {
    const benchmarks = [benchmark("equal_weight_monthly")];
    expect(resolvePrimaryBenchmark(benchmarks)?.key).toBe("equal_weight_monthly");
  });

  it("returns null for an empty benchmark collection", () => {
    expect(resolvePrimaryBenchmark([])).toBeNull();
  });
});

describe("computeMetricDifference", () => {
  it("subtracts finite strategy and benchmark values", () => {
    expect(computeMetricDifference("1.5", "0.8")).toBeCloseTo(0.7);
    expect(computeMetricDifference("-0.09", "-0.08")).toBeCloseTo(-0.01);
  });

  it("propagates null when either side is null", () => {
    expect(computeMetricDifference(null, "0.8")).toBeNull();
    expect(computeMetricDifference("1.5", null)).toBeNull();
    expect(computeMetricDifference(null, null)).toBeNull();
  });

  it("propagates null when either side is non-finite", () => {
    expect(computeMetricDifference("not-a-number", "0.8")).toBeNull();
    expect(computeMetricDifference("1.5", "Infinity")).toBeNull();
  });

  it("parses metric numbers only when finite", () => {
    expect(parseMetricNumber("0.02")).toBeCloseTo(0.02);
    expect(parseMetricNumber(null)).toBeNull();
    expect(parseMetricNumber("NaN")).toBeNull();
  });
});

describe("computeVerdict", () => {
  it("returns Outperforming when all valid differences are non-negative with at least one positive", () => {
    expect(computeVerdict([0.04, 0.03, 0.7, 0.01])).toBe("Outperforming");
    expect(computeVerdict([0, 0.03, 0, 0.01])).toBe("Outperforming");
  });

  it("returns Underperforming when all valid differences are non-positive with at least one negative", () => {
    expect(computeVerdict([-0.04, -0.03, -0.7, -0.01])).toBe("Underperforming");
    expect(computeVerdict([0, -0.03, 0, -0.01])).toBe("Underperforming");
  });

  it("returns Mixed for a positive/negative sign mix", () => {
    expect(computeVerdict([0.04, -0.03, 0.7, -0.01])).toBe("Mixed");
  });

  it("returns Mixed for all-zero valid differences", () => {
    expect(computeVerdict([0, 0])).toBe("Mixed");
  });

  it("withholds the verdict with fewer than two valid differences", () => {
    expect(computeVerdict([null, null, null, null])).toBeNull();
    expect(computeVerdict([0.04, null, null, null])).toBeNull();
    expect(computeVerdict([0.04, -0.03, null, null])).toBe("Mixed");
  });
});

describe("formatParametersHumanReadable", () => {
  it("maps known keys to documented labels and formatting", () => {
    const entries = formatParametersHumanReadable(
      JSON.stringify({
        strategy_id: "dual-momentum-1",
        config_version: "v2",
        type: "dual_momentum",
        start_date: "2026-01-01",
        end_date: "2026-01-02",
        risk_free_rate: 0.02,
        performance_metric_version: "perf_v3",
        equity_model_version: "eq_v2",
        tail_distribution_metric_version: "tail_v1",
        benchmark_regime_metric_version: "regime_v1"
      })
    );

    expect(entries).toEqual([
      { key: "strategy_id", label: "Strategy", value: "dual-momentum-1" },
      { key: "config_version", label: "Config version", value: "v2" },
      { key: "type", label: "Strategy type", value: "Dual momentum" },
      { key: "start_date", label: "Start date", value: "2026-01-01" },
      { key: "end_date", label: "End date", value: "2026-01-02" },
      { key: "risk_free_rate", label: "Annualized risk-free rate", value: "2.0%" },
      { key: "performance_metric_version", label: "Performance metric version", value: "perf_v3" },
      { key: "equity_model_version", label: "Equity model version", value: "eq_v2" },
      { key: "tail_distribution_metric_version", label: "Tail distribution metric version", value: "tail_v1" },
      { key: "benchmark_regime_metric_version", label: "Benchmark regime metric version", value: "regime_v1" }
    ]);
  });

  it("renders the annualized risk-free rate as a percentage", () => {
    const entries = formatParametersHumanReadable(
      JSON.stringify({ risk_free_rate: 0.02 })
    );
    expect(entries[0]).toEqual({
      key: "risk_free_rate",
      label: "Annualized risk-free rate",
      value: "2.0%"
    });
  });

  it("falls back to raw key and value text for unknown keys", () => {
    const entries = formatParametersHumanReadable(
      JSON.stringify({ custom_flag: "raw-value", nested: { a: 1 } })
    );
    expect(entries).toEqual([
      { key: "custom_flag", label: "custom_flag", value: "raw-value" },
      { key: "nested", label: "nested", value: '{"a":1}' }
    ]);
  });

  it("returns an empty list for null or malformed payloads", () => {
    expect(formatParametersHumanReadable(null)).toEqual([]);
    expect(formatParametersHumanReadable("not-json")).toEqual([]);
    expect(formatParametersHumanReadable("[1,2]")).toEqual([]);
  });
});
