import type {
  DashboardBacktestSummary,
  DashboardResponse,
  DashboardWalkForwardOos,
  DashboardWalkForwardSummary
} from "../api/client";
import {
  EMPTY_VALUE,
  formatDate,
  formatDecimal,
  formatInteger,
  formatRatioAsPercent
} from "../utils/formatters";
import {
  computeMetricDifference,
  formatDrawdownDifference,
  formatSignedDecimal,
  formatSignedPercent,
  resolvePrimaryBenchmark as resolvePrimaryBenchmarkFromList
} from "./backtestFormatters";
import {
  formatPercentNumber,
  resolvePrimaryBenchmark as resolvePrimaryBenchmarkFromMap,
  TAIL_OWNER_LABELS
} from "./walkForwardFormatters";

/** Element ids of the pre-existing Dashboard operation controls. The
 *  current-state layer links to these instead of duplicating their triggers,
 *  so no operation can be started twice and no new application state is
 *  introduced. */
export const RESEARCH_ACTION_TARGET_IDS = {
  fetchMarketData: "dashboard-fetch-market-data",
  generateSignal: "dashboard-generate-signal",
  runBacktest: "dashboard-run-backtest"
} as const;

export type ResearchFact = {
  key: "market_data" | "signal" | "backtest" | "walk_forward";
  label: string;
  value: string;
  /** Calendar days this artifact trails the market-data cutoff. Null when the
   *  artifact is missing, the cutoff is unknown, or the artifact is not behind
   *  it. Calendar days are deliberately not trading-session days. */
  lagCalendarDays: number | null;
  isMissing: boolean;
};

export type ResearchNextAction = {
  label: string;
  targetId: string;
};

/** Whole calendar days from `earlier` to `later` for two ISO `YYYY-MM-DD`
 *  dates. Returns null when either value is not a date. This is a date
 *  difference, not a financial value. */
export function calendarDaysBetween(earlier: string, later: string): number | null {
  const start = Date.parse(`${earlier.slice(0, 10)}T00:00:00Z`);
  const end = Date.parse(`${later.slice(0, 10)}T00:00:00Z`);
  if (!Number.isFinite(start) || !Number.isFinite(end)) {
    return null;
  }
  return Math.round((end - start) / 86_400_000);
}

/** Calendar days an artifact trails the market-data cutoff, or null when the
 *  artifact is missing, the cutoff is unknown, or the artifact is current. */
function lagBehindCutoff(
  artifactDate: string | null,
  cutoff: string | null
): number | null {
  if (artifactDate === null || cutoff === null) {
    return null;
  }
  const days = calendarDaysBetween(artifactDate, cutoff);
  return days === null || days <= 0 ? null : days;
}

/** The four current-state facts. Every value comes from an aggregate field;
 *  no performance or risk value is derived here. */
export function deriveResearchFacts(data: DashboardResponse): ResearchFact[] {
  const cutoff = data.market_data.latest_trade_date;
  const signal = data.latest_signal;
  const backtest = data.recent_backtest;
  const walkForward = data.latest_walk_forward;

  return [
    {
      key: "market_data",
      label: "Market data",
      value:
        cutoff === null
          ? "No price rows stored"
          : `Stored through ${formatDate(cutoff)}`,
      lagCalendarDays: null,
      isMissing: data.market_data.price_rows === 0
    },
    {
      key: "signal",
      label: "Latest signal",
      value: signal === null ? "No successful signal" : `Signalled for ${formatDate(signal.signal_date)}`,
      lagCalendarDays:
        signal === null ? null : lagBehindCutoff(signal.signal_date, cutoff),
      isMissing: signal === null
    },
    {
      key: "backtest",
      label: "Latest backtest",
      value:
        backtest === null
          ? "No backtest run"
          : `${formatDate(backtest.start_date)} to ${formatDate(backtest.end_date)}`,
      lagCalendarDays:
        backtest === null ? null : lagBehindCutoff(backtest.end_date, cutoff),
      isMissing: backtest === null
    },
    {
      key: "walk_forward",
      label: "Walk-forward",
      value: describeWalkForwardState(walkForward),
      lagCalendarDays: null,
      isMissing: walkForward === null
    }
  ];
}

/** The single next research action, or null when nothing is missing or
 *  lagging. The backtest range is a deliberate research choice, so a short
 *  range never triggers an action. */
export function selectNextResearchAction(
  data: DashboardResponse,
  facts: ResearchFact[]
): ResearchNextAction | null {
  const marketData = facts.find((fact) => fact.key === "market_data");
  if (marketData?.isMissing) {
    return { label: "Fetch market data", targetId: RESEARCH_ACTION_TARGET_IDS.fetchMarketData };
  }

  const signal = facts.find((fact) => fact.key === "signal");
  if (signal === undefined) {
    return null;
  }
  if (signal.isMissing) {
    return { label: "Generate signal", targetId: RESEARCH_ACTION_TARGET_IDS.generateSignal };
  }
  if (signal.lagCalendarDays !== null) {
    return { label: "Generate signal", targetId: RESEARCH_ACTION_TARGET_IDS.generateSignal };
  }

  if (data.recent_backtest === null) {
    return { label: "Run a backtest", targetId: RESEARCH_ACTION_TARGET_IDS.runBacktest };
  }

  return null;
}

export function describeWalkForwardState(
  walkForward: DashboardWalkForwardSummary | null
): string {
  if (walkForward === null) {
    return "No run yet";
  }
  const label = walkForwardStatusLabel(walkForward.status);
  return walkForward.window_count > 0
    ? `${label} · ${formatInteger(walkForward.window_count)} windows`
    : label;
}

export function walkForwardStatusLabel(status: string): string {
  if (status === "queued") return "Queued";
  if (status === "running") return "Running";
  if (status === "success") return "Completed";
  if (status === "failed") return "Failed";
  return status;
}

export type PerformanceHeadline = {
  key: string;
  label: string;
  value: string;
  /** Signed difference against the primary benchmark, or null when the run has
   *  no benchmark evidence. */
  difference: string | null;
};

export type PerformanceEvidence = {
  primaryBenchmarkName: string | null;
  headlines: PerformanceHeadline[];
};

/** Four headline values plus their difference against the run's primary
 *  benchmark. Return differences use the backend-published difference fields;
 *  Sharpe and drawdown differences are display-level subtraction of two
 *  published values. */
export function derivePerformanceEvidence(
  backtest: DashboardBacktestSummary
): PerformanceEvidence {
  const primary = resolvePrimaryBenchmarkFromList(backtest.benchmarks);

  const headlines: PerformanceHeadline[] = [
    {
      key: "total_return",
      label: "Total return",
      value: formatRatioAsPercent(backtest.total_return),
      difference: primary ? formatSignedPercent(primary.total_return_difference) : null
    },
    {
      key: "annualized_return",
      label: "CAGR (calendar-time)",
      value: formatRatioAsPercent(backtest.annualized_return),
      difference: primary
        ? formatSignedPercent(primary.annualized_return_difference)
        : null
    },
    {
      key: "sharpe_ratio",
      label: "Sharpe (daily returns, 252D)",
      value: formatDecimal(backtest.sharpe_ratio, 2, false),
      difference: primary
        ? formatSignedDecimal(
            computeMetricDifference(backtest.sharpe_ratio, primary.sharpe_ratio)
          )
        : null
    },
    {
      key: "max_drawdown",
      label: "Max drawdown",
      value: formatRatioAsPercent(backtest.max_drawdown),
      difference: primary
        ? formatDrawdownDifference(backtest.max_drawdown, primary.max_drawdown)
        : null
    }
  ];

  return {
    primaryBenchmarkName: primary ? primary.name : null,
    headlines
  };
}

export type OosHeadline = {
  label: string;
  value: string;
  meta: string;
};

/** Cross-window OOS headline values, each rendered from a persisted evidence
 *  field. No value is computed here. */
export function deriveOosHeadlines(oos: DashboardWalkForwardOos): OosHeadline[] {
  const totalReturn = oos.metrics.total_return;
  const primary = resolvePrimaryBenchmarkFromMap(oos.benchmarks);

  return [
    {
      label: "OOS total return",
      value: formatPercentNumber(totalReturn.median),
      meta: `median · mean ${formatPercentNumber(totalReturn.mean)}`
    },
    {
      label: "OOS median Sharpe",
      value: ratioValue(oos.metrics.sharpe_ratio.median),
      meta: `${formatInteger(oos.metrics.sharpe_ratio.valid_count)}/${formatInteger(
        oos.metrics.sharpe_ratio.window_count
      )} valid windows`
    },
    {
      label: "OOS max drawdown",
      value: formatPercentNumber(oos.metrics.max_drawdown.median),
      meta: `median across ${formatInteger(oos.metrics.max_drawdown.window_count)} windows`
    },
    {
      label: "Positive window rate",
      value: formatPercentNumber(oos.positive_window_rate.value),
      meta: `${formatInteger(oos.positive_window_rate.numerator)}/${formatInteger(
        oos.positive_window_rate.denominator
      )} windows`
    },
    {
      label: "Benchmark outperformance",
      value: primary
        ? formatPercentNumber(primary.benchmark.outperformance_rate.value)
        : EMPTY_VALUE,
      meta: primary
        ? `vs ${TAIL_OWNER_LABELS[primary.key] ?? primary.key} · ${formatInteger(
            primary.benchmark.outperformance_rate.numerator
          )}/${formatInteger(primary.benchmark.outperformance_rate.denominator)} windows`
        : "No benchmark evidence"
    }
  ];
}

function ratioValue(value: number | null): string {
  return value === null ? EMPTY_VALUE : value.toFixed(2);
}

/** Explains why a walk-forward run has no OOS evidence, in terms of the run's
 *  own status. */
export function describeOosAvailability(walkForward: DashboardWalkForwardSummary): string {
  if (walkForward.status === "failed") {
    return walkForward.error_message === null
      ? "Evidence is unavailable because this run failed."
      : `Evidence is unavailable because this run failed: ${walkForward.error_message}`;
  }
  return `Evidence is unavailable until this ${walkForward.status} run reaches a terminal state.`;
}
