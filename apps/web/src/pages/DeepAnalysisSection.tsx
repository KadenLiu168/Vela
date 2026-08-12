import type {
  BacktestBenchmark,
  BacktestDetailMetrics,
  ReturnStability
} from "../api/client";
import { formatDecimal, formatNullableInteger, formatRatioAsPercent } from "../utils/formatters";
import { DistributionRiskSection } from "./DistributionRiskSection";
import { ReturnStabilitySection } from "./ReturnStabilitySection";

type DeepAnalysisSectionProps = {
  metrics: BacktestDetailMetrics;
  benchmarks: BacktestBenchmark[];
  returnStability: ReturnStability;
};

/**
 * Deep Analysis region assembling the secondary evidence groups: one-day
 * historical distribution risk (strategy and each benchmark), return stability,
 * and CSI-300 CAPM. Each group keeps its own closed-by-default disclosure; the
 * region itself is only a labeled container, not a nested disclosure.
 */
export function DeepAnalysisSection({
  metrics,
  benchmarks,
  returnStability
}: DeepAnalysisSectionProps) {
  const csi300 = benchmarks.find((benchmark) => benchmark.key === "csi_300_buy_hold");

  return (
    <section
      aria-labelledby="deep-analysis-heading"
      className="holdings-section"
    >
      <h3 id="deep-analysis-heading">Deep analysis</h3>
      <DistributionRiskSection fields={metrics} />
      {benchmarks.map((benchmark) => (
        <DistributionRiskSection
          fields={benchmark}
          key={benchmark.key}
          ownerName={benchmark.name}
        />
      ))}
      <ReturnStabilitySection stability={returnStability} />
      {csi300 ? <CapmSection benchmark={csi300} /> : null}
    </section>
  );
}

/** CSI-300-only CAPM evidence in a closed-by-default disclosure. */
function CapmSection({ benchmark }: { benchmark: BacktestBenchmark }) {
  return (
    <details className="disclosure">
      <summary className="disclosure-summary">
        <h4 className="disclosure-heading">CSI-300 CAPM regression</h4>
      </summary>
      <div className="disclosure-body">
        <dl className="metric-card-grid">
          <MetricCard
            label="CSI 300 ETF proxy Alpha (252D compounded)"
            value={formatRatioAsPercent(benchmark.capm_alpha)}
          />
          <MetricCard
            label="Beta (CSI 300 ETF proxy)"
            value={formatDecimal(benchmark.capm_beta, 6, false)}
          />
          <MetricCard
            label="R-squared (CSI 300 ETF proxy)"
            value={formatDecimal(benchmark.capm_r_squared, 6, false)}
          />
          <MetricCard
            label="CAPM observations (daily sessions)"
            value={formatNullableInteger(benchmark.capm_observation_count)}
          />
        </dl>
      </div>
    </details>
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
