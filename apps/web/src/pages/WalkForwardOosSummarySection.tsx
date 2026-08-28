import type {
  WalkForwardDetailResponse,
  WalkForwardRunStatus
} from "../api/client";
import {
  aggregateTransitionRate,
  formatPercentNumber,
  generalizationGapText,
  resolvePrimaryBenchmark,
  TAIL_OWNER_LABELS
} from "./walkForwardFormatters";

type WalkForwardOosSummarySectionProps = {
  evidence: WalkForwardDetailResponse["evidence"];
  status: WalkForwardRunStatus;
};

function formatRatio(value: number | null): string {
  return value === null ? "n/a" : value.toFixed(2);
}

/** First-screen OOS Summary: six headline cards sourced entirely from
 *  persisted cross-window evidence fields plus an explained fact line for
 *  the Generalization Gap and Evidence Status. No new financial metric is
 *  computed in the browser. */
export function WalkForwardOosSummarySection({
  evidence,
  status
}: WalkForwardOosSummarySectionProps) {
  if (evidence === null) {
    return (
      <section className="holdings-section" aria-labelledby="walk-forward-oos-summary-heading">
        <h2 id="walk-forward-oos-summary-heading">OOS summary</h2>
        <p className="detail-note">
          {status === "failed"
            ? "Evidence is unavailable because this run failed."
            : `Evidence is unavailable until this ${status} run reaches a terminal state.`}
        </p>
      </section>
    );
  }

  const totalReturn = evidence.metrics.total_return;
  const positiveRate = evidence.positive_window_rate;
  const primary = resolvePrimaryBenchmark(evidence.benchmarks);
  const transition = aggregateTransitionRate(evidence.parameter_stability);

  return (
    <section className="holdings-section" aria-labelledby="walk-forward-oos-summary-heading">
      <h2 id="walk-forward-oos-summary-heading">OOS summary</h2>
      <dl aria-label="OOS summary headline metrics" className="oos-summary-grid">
        <div className="metric-card">
          <dt>OOS total return</dt>
          <dd>{formatPercentNumber(totalReturn.median)}</dd>
          <p className="oos-summary-card-sub">mean {formatPercentNumber(totalReturn.mean)}</p>
          <p className="oos-summary-card-meta">median across {totalReturn.window_count} windows</p>
        </div>
        <div className="metric-card">
          <dt>OOS median Sharpe</dt>
          <dd>{formatRatio(evidence.metrics.sharpe_ratio.median)}</dd>
        </div>
        <div className="metric-card">
          <dt>OOS max drawdown</dt>
          <dd>{formatPercentNumber(evidence.metrics.max_drawdown.median)}</dd>
        </div>
        <div className="metric-card">
          <dt>Positive window rate</dt>
          <dd>{formatPercentNumber(positiveRate.value)}</dd>
          <p className="oos-summary-card-meta">
            {positiveRate.numerator}/{positiveRate.denominator} windows
          </p>
        </div>
        <div className="metric-card">
          <dt>Benchmark outperformance</dt>
          <dd>{primary ? formatPercentNumber(primary.benchmark.outperformance_rate.value) : "n/a"}</dd>
          {primary ? (
            <p className="oos-summary-card-meta">
              vs {TAIL_OWNER_LABELS[primary.key] ?? primary.key} ·{" "}
              {primary.benchmark.outperformance_rate.numerator}/
              {primary.benchmark.outperformance_rate.denominator} windows
            </p>
          ) : null}
        </div>
        <div className="metric-card">
          <dt>Max parameter transition</dt>
          <dd>{transition ? formatPercentNumber(transition.rate) : "n/a"}</dd>
          {transition ? (
            <p className="oos-summary-card-meta">
              {transition.parameterName} · {transition.comparisonCount} comparisons
            </p>
          ) : null}
        </div>
      </dl>
      <div className="fact-line">
        <p>{generalizationGapText(evidence.generalization_gap)}</p>
        <p>
          Evidence status: {evidence.metrics.total_return.evidence_status} — sufficient requires
          at least three valid windows.
        </p>
      </div>
    </section>
  );
}
