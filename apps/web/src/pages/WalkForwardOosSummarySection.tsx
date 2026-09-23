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
  const headlineCards = [
    {
      label: "OOS total return",
      value: formatPercentNumber(totalReturn.median),
      sub: `mean ${formatPercentNumber(totalReturn.mean)}`,
      meta: `median across ${totalReturn.window_count} windows`
    },
    {
      label: "OOS median Sharpe",
      value: formatRatio(evidence.metrics.sharpe_ratio.median)
    },
    {
      label: "OOS max drawdown",
      value: formatPercentNumber(evidence.metrics.max_drawdown.median)
    },
    {
      label: "Positive window rate",
      value: formatPercentNumber(positiveRate.value),
      meta: `${positiveRate.numerator}/${positiveRate.denominator} windows`
    },
    {
      label: "Benchmark outperformance",
      value: primary ? formatPercentNumber(primary.benchmark.outperformance_rate.value) : "n/a",
      meta: primary
        ? `vs ${TAIL_OWNER_LABELS[primary.key] ?? primary.key} · ${primary.benchmark.outperformance_rate.numerator}/${primary.benchmark.outperformance_rate.denominator} windows`
        : undefined
    },
    {
      label: "Max parameter transition",
      value: transition ? formatPercentNumber(transition.rate) : "n/a",
      meta: transition ? `${transition.parameterName} · ${transition.comparisonCount} comparisons` : undefined
    }
  ];

  return (
    <section className="holdings-section" aria-labelledby="walk-forward-oos-summary-heading">
      <h2 id="walk-forward-oos-summary-heading">OOS summary</h2>
      <dl aria-label="OOS summary headline metrics" className="oos-summary-grid">
        {headlineCards.map((card) => (
          <div className="metric-card" key={card.label}>
            <dt>{card.label}</dt>
            <dd>
              {card.value}
              {card.sub ? <p className="oos-summary-card-sub">{card.sub}</p> : null}
              {card.meta ? <p className="oos-summary-card-meta">{card.meta}</p> : null}
            </dd>
          </div>
        ))}
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
