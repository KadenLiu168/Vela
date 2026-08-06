import type { TailDistributionFields } from "../api/client";
import { formatDecimal, formatNullableInteger } from "../utils/formatters";

/**
 * Presents stored one-day historical distribution-risk evidence (VaR/CVaR as
 * positive loss magnitudes, skewness, excess kurtosis with the normal baseline
 * of zero) plus observation/tail counts. The browser never recomputes metrics:
 * values come from the API and only the evidence note is derived from the
 * stored counts and nulls.
 */
export function DistributionRiskSection({ fields }: { fields: TailDistributionFields }) {
  return (
    <section className="holdings-section" aria-labelledby="distribution-risk-heading">
      <h4 id="distribution-risk-heading">One-day historical distribution risk (95%)</h4>
      <dl className="metric-card-grid">
        <MetricCard label="Historical VaR 95% (1D loss)" value={formatDecimal(fields.historical_var_95, 6, false)} />
        <MetricCard label="Historical CVaR 95% (1D loss)" value={formatDecimal(fields.historical_cvar_95, 6, false)} />
        <MetricCard label="Skewness" value={formatDecimal(fields.return_skewness, 6, false)} />
        <MetricCard
          label="Excess kurtosis (normal = 0)"
          value={formatDecimal(fields.return_excess_kurtosis, 6, false)}
        />
        <MetricCard
          label="Effective observations"
          value={formatNullableInteger(fields.distribution_observation_count)}
        />
        <MetricCard
          label="Tail observations (5% rank rule)"
          value={formatNullableInteger(fields.tail_observation_count)}
        />
      </dl>
      <p className="distribution-evidence-note">{distributionNote(fields)}</p>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function distributionNote(fields: TailDistributionFields): string {
  if (fields.distribution_evidence_status === "unavailable_legacy") {
    return "Legacy history: one-day historical distribution metrics were not recorded for this run.";
  }
  if (fields.distribution_evidence_status === "insufficient_evidence") {
    const tailCount = fields.tail_observation_count ?? 0;
    return (
      "Insufficient evidence: publication requires at least 100 effective observations. " +
      `The displayed tail count of ${tailCount} is the cardinality implied by the fixed 5% ` +
      "rank rule; no tail metric is published from it."
    );
  }
  if (fields.return_skewness === null || fields.return_excess_kurtosis === null) {
    return (
      "Constant distribution: return shape statistics are undefined (zero second central " +
      "moment); VaR and CVaR remain published."
    );
  }
  return (
    "One-day historical positive losses and descriptive shape statistics. No forecast or " +
    "regulatory-capital claim is made."
  );
}
