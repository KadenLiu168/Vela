import type { BacktestBenchmark, BacktestDetailMetrics } from "../api/client";
import {
  EMPTY_VALUE,
  formatDecimal,
  formatRatioAsPercent
} from "../utils/formatters";
import {
  computeMetricDifference,
  computeVerdict,
  parseMetricNumber,
  resolvePrimaryBenchmark,
  type Verdict
} from "./backtestFormatters";

type DecisionSummarySectionProps = {
  metrics: BacktestDetailMetrics;
  benchmarks: BacktestBenchmark[];
};

type HeadlineMetric = {
  key: string;
  label: string;
  value: string;
};

/** Signed percent difference (return-style evidence), e.g. "+2.00%". */
function formatSignedPercent(value: string | null): string {
  const parsed = parseMetricNumber(value);
  if (parsed === null) {
    return EMPTY_VALUE;
  }
  const percent = parsed * 100;
  const sign = percent > 0 ? "+" : "";
  return `${sign}${percent.toFixed(2)}%`;
}

/** Signed decimal difference (Sharpe-style evidence), e.g. "+0.70". */
function formatSignedDecimal(value: number | null): string {
  if (value === null) {
    return EMPTY_VALUE;
  }
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}`;
}

/** Max drawdown difference framed as shallower/deeper: a value closer to zero
 *  is favorable, so a positive difference means the strategy drawdown is
 *  shallower than the primary benchmark's. The sign never stands alone as a
 *  naked difference. */
function formatDrawdownDifference(
  strategyValue: string | null,
  benchmarkValue: string | null
): string {
  const difference = computeMetricDifference(strategyValue, benchmarkValue);
  if (difference === null) {
    return EMPTY_VALUE;
  }
  const magnitude = `${(Math.abs(difference) * 100).toFixed(2)}%`;
  if (difference === 0) {
    return "in line";
  }
  return difference > 0 ? `shallower by ${magnitude}` : `deeper by ${magnitude}`;
}

/**
 * First-screen Decision Summary: the strategy's four headline values plus their
 * difference versus the Primary Benchmark. CAGR and Total return differences
 * use the backend-provided difference fields; Sharpe and Max drawdown
 * differences are display-level subtraction of non-null API values. A
 * sign-derived verdict badge translates the difference signs; it is withheld
 * (null) unless at least two valid differences are present.
 */
export function DecisionSummarySection({
  metrics,
  benchmarks
}: DecisionSummarySectionProps) {
  const primary = resolvePrimaryBenchmark(benchmarks);

  const headlineMetrics: HeadlineMetric[] = [
    {
      key: "total_return",
      label: "Total return",
      value: formatRatioAsPercent(metrics.total_return)
    },
    {
      key: "annualized_return",
      label: "CAGR (calendar-time)",
      value: formatRatioAsPercent(metrics.annualized_return)
    },
    {
      key: "sharpe_ratio",
      label: "Sharpe (daily returns, 252D)",
      value: formatDecimal(metrics.sharpe_ratio, 2, false)
    },
    {
      key: "max_drawdown",
      label: "Max drawdown",
      value: formatRatioAsPercent(metrics.max_drawdown)
    }
  ];

  const differenceByKey: Record<string, string> = primary
    ? {
        total_return: formatSignedPercent(primary.total_return_difference),
        annualized_return: formatSignedPercent(primary.annualized_return_difference),
        sharpe_ratio: formatSignedDecimal(
          computeMetricDifference(metrics.sharpe_ratio, primary.sharpe_ratio)
        ),
        max_drawdown: formatDrawdownDifference(
          metrics.max_drawdown,
          primary.max_drawdown
        )
      }
    : {};

  const verdict: Verdict | null = primary
    ? computeVerdict([
        parseMetricNumber(primary.total_return_difference),
        parseMetricNumber(primary.annualized_return_difference),
        computeMetricDifference(metrics.sharpe_ratio, primary.sharpe_ratio),
        computeMetricDifference(metrics.max_drawdown, primary.max_drawdown)
      ])
    : null;

  return (
    <section
      aria-labelledby="decision-summary-heading"
      className="decision-summary-section"
    >
      <div className="decision-summary-header">
        <h3 id="decision-summary-heading">Decision summary</h3>
        {verdict ? (
          <span className={`verdict-badge verdict-badge-${verdict.toLowerCase()}`}>
            {verdict}
          </span>
        ) : null}
      </div>
      <p className="detail-note">
        {primary
          ? `Primary benchmark: ${primary.name}. Differences are sign-only display evidence; full values remain in the benchmark comparison below.`
          : "No benchmark is available; the four strategy values stand alone."}
      </p>
      <div aria-label="Strategy decision summary metrics" className="metric-card-grid">
        {headlineMetrics.map((metric) => (
          <div className="metric-card" key={metric.key}>
            <dt>{metric.label}</dt>
            <dd>{metric.value}</dd>
            {primary ? (
              <p className="decision-difference">
                vs {primary.name}: {differenceByKey[metric.key]}
              </p>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}
