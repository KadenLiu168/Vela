import type {
  WalkForwardBenchmarkEvidence,
  WalkForwardBenchmarkKey,
  WalkForwardEvidence,
  WalkForwardMetricSummary
} from "../api/client";

export const TAIL_OWNER_LABELS: Record<string, string> = {
  strategy: "Strategy",
  equal_weight_monthly: "Equal-weight monthly",
  csi_300_buy_hold: "CSI 300 buy-and-hold"
};

/** Percentage formatting for WalkForward metric numbers: 0.0234 -> "2.34%";
 *  null -> "n/a". Covers return-like metrics (total return / max drawdown)
 *  and rate metrics in the OOS Summary. */
export function formatPercentNumber(value: number | null, digits = 2): string {
  if (value === null) {
    return "n/a";
  }
  return `${(value * 100).toFixed(digits)}%`;
}

export type WalkForwardPrimaryBenchmark = {
  key: WalkForwardBenchmarkKey;
  benchmark: WalkForwardBenchmarkEvidence;
};

/** Primary benchmark for the OOS Summary outperformance card: the CSI-300
 *  buy-and-hold key when present, otherwise the first benchmark in the
 *  collection, otherwise null (no benchmarks). Mirrors the backtest detail
 *  priority rule, adapted to the walk-forward record input shape. */
export function resolvePrimaryBenchmark(
  benchmarks: Record<WalkForwardBenchmarkKey, WalkForwardBenchmarkEvidence>
): WalkForwardPrimaryBenchmark | null {
  const keys = Object.keys(benchmarks) as WalkForwardBenchmarkKey[];
  if (keys.length === 0) {
    return null;
  }
  const key = keys.includes("csi_300_buy_hold") ? "csi_300_buy_hold" : keys[0];
  return { key, benchmark: benchmarks[key] };
}

export type TransitionRateAggregate = {
  rate: number;
  parameterName: string;
  comparisonCount: number;
};

/** Maximum per-parameter transition rate across the parameter-stability
 *  record, carrying the parameter name and comparison count so a
 *  low-comparison base cannot be misread as an unstable parameter. Null
 *  rates (parameters with no comparisons) are skipped; ties keep the first
 *  parameter in insertion order (the backend emits sorted names). Returns
 *  null when no parameter has a transition rate. */
export function aggregateTransitionRate(
  parameterStability: WalkForwardEvidence["parameter_stability"]
): TransitionRateAggregate | null {
  let max: TransitionRateAggregate | null = null;
  for (const [name, stability] of Object.entries(parameterStability)) {
    if (stability.transition_rate === null) {
      continue;
    }
    if (max === null || stability.transition_rate > max.rate) {
      max = {
        rate: stability.transition_rate,
        parameterName: name,
        comparisonCount: stability.comparison_count
      };
    }
  }
  return max;
}

/** Explained Generalization Gap fact line. The gap is the per-window
 *  IS-minus-OOS Sharpe difference aggregated across windows (a Sharpe
 *  difference, ratio units, not a percentage); a positive value means
 *  in-sample selection performed better than out-of-sample and a larger
 *  gap indicates weaker generalization. */
export function generalizationGapText(summary: WalkForwardMetricSummary): string {
  const median = summary.median === null ? "n/a" : summary.median.toFixed(2);
  return (
    `Generalization gap (IS Sharpe − OOS Sharpe): median ${median} — ` +
    "a positive gap means in-sample selection performed better than out-of-sample; " +
    "the larger the gap, the weaker the generalization."
  );
}
