import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ApiClientError,
  type WalkForwardBenchmark,
  type WalkForwardDetailResponse,
  type WalkForwardMetricSummary,
  getWalkForwardDetail
} from "../api/client";
import { DescriptionItem, EmptyState, FeedbackMessage } from "../components";
import {
  formatDate,
  formatDecimal,
  formatInteger,
  formatNullableInteger,
  formatNullableText,
  formatTimestamp
} from "../utils/formatters";
import { computeEquityCurveGeometry, EQUITY_CURVE_CHART, normalizeEquityCurvePoints } from "./equityCurveChart";

type WalkForwardDetailPageProps = {
  runId: string;
};

type WalkForwardDetailState =
  | { status: "loading"; data?: never; error?: never; runId?: never }
  | { status: "ready"; data: WalkForwardDetailResponse; error?: never; runId: string }
  | { status: "not-found"; data?: never; error?: never; runId: string }
  | { status: "error"; data?: never; error: string; runId: string };

type PersistedWalkForwardEvidence = NonNullable<WalkForwardDetailResponse["evidence"]>;

const metricLabels: Record<string, string> = {
  total_return: "Total return",
  annualized_return: "Annualized return",
  max_drawdown: "Max drawdown",
  volatility: "Volatility",
  sharpe_ratio: "Sharpe ratio",
  sortino_ratio: "Sortino ratio",
  calmar_ratio: "Calmar ratio",
  longest_drawdown_duration_sessions: "Longest drawdown duration"
};

export function WalkForwardDetailPage({ runId }: WalkForwardDetailPageProps) {
  const [state, setState] = useState<WalkForwardDetailState>({ status: "loading" });

  useEffect(() => {
    let isCurrent = true;

    getWalkForwardDetail(runId)
      .then((data) => {
        if (isCurrent) {
          setState({ status: "ready", data, runId });
        }
      })
      .catch((error: unknown) => {
        if (!isCurrent) {
          return;
        }

        if (error instanceof ApiClientError && error.status === 404) {
          setState({ status: "not-found", runId });
          return;
        }

        setState({
          status: "error",
          error: error instanceof ApiClientError ? error.kind : "unavailable",
          runId
        });
      });

    return () => {
      isCurrent = false;
    };
  }, [runId]);

  const currentState = state.status === "loading" || state.runId === runId ? state : { status: "loading" as const };

  return (
    <section className="page detail-page walk-forward-detail-page">
      <div className="page-heading">
        <p>Walk-forward research workspace</p>
        <h1>Walk-forward #{runId}</h1>
      </div>
      {renderDetail(currentState, runId)}
    </section>
  );
}

function renderDetail(state: WalkForwardDetailState, runId: string) {
  if (state.status === "loading") {
    return <FeedbackMessage variant="loading">Loading Walk-forward detail.</FeedbackMessage>;
  }

  if (state.status === "not-found") {
    return <EmptyState>Walk-forward run {runId} was not found.</EmptyState>;
  }

  if (state.status === "error") {
    return (
      <FeedbackMessage className="dashboard-alert" variant="error">
        Walk-forward detail API unavailable: {state.error}
      </FeedbackMessage>
    );
  }

  const { data } = state;
  return (
    <article className="dashboard-panel">
      <strong className="panel-primary">Persisted evaluation evidence</strong>
      <RunSummary data={data} />
      <EvidenceSection data={data} />
      <StitchedOosSection data={data} />
      <ProvenanceSection data={data} />
      <WindowSection data={data} />
    </article>
  );
}

function StitchedOosSection({ data }: { data: WalkForwardDetailResponse }) {
  const stitched = data.stitched_oos;
  if (stitched === null) {
    return null;
  }
  if (stitched.status === "unavailable_non_contiguous_windows") {
    return <section className="holdings-section" aria-labelledby="stitched-oos-heading"><h2 id="stitched-oos-heading">Stitched OOS capital path</h2><p className="detail-note">Gap or overlap windows cannot form one chronological capital path. Independent OOS evidence remains available below.</p></section>;
  }
  const chartPoints = normalizeEquityCurvePoints(stitched.points);
  const geometry = chartPoints.length > 1 ? computeEquityCurveGeometry(chartPoints) : null;
  const resets = stitched.points.filter((point) => point.is_window_start);
  return <section className="holdings-section" aria-labelledby="stitched-oos-heading">
    <h2 id="stitched-oos-heading">Stitched OOS capital path</h2>
    <p className="detail-note">Compounds separately initialized OOS segments. No seam return, holdings carry, turnover, or transaction cost is synthesized.</p>
    <dl className="compact-list"><DescriptionItem label="Ending net value" value={stitched.ending_net_value ?? "n/a"} /><DescriptionItem label="Cumulative total return" value={stitched.total_return ?? "n/a"} /></dl>
    {geometry ? <svg aria-label="Stitched OOS equity curve" className="equity-curve-chart" role="img" viewBox={`0 0 ${EQUITY_CURVE_CHART.width} ${EQUITY_CURVE_CHART.height}`}><path className="equity-curve-line" d={geometry.linePath} fill="none" stroke="var(--color-acid-lime)" /></svg> : <EmptyState>No valid stitched OOS curve points are available for this run.</EmptyState>}
    <ul aria-label="Stitched OOS window resets">{resets.map((point) => <li key={`${point.window_ordinal}-${point.trade_date}`}>Window {point.window_ordinal + 1} reset: {formatDate(point.trade_date)}</li>)}</ul>
  </section>;
}

function RunSummary({ data }: { data: WalkForwardDetailResponse }) {
  const { run } = data;
  return (
    <section className="holdings-section" aria-labelledby="walk-forward-run-heading">
      <h2 id="walk-forward-run-heading">Execution</h2>
      <dl className="compact-list">
        <DescriptionItem label="Strategy" value={run.strategy_id} />
        <DescriptionItem label="Date range" value={`${formatDate(run.start_date)} to ${formatDate(run.end_date)}`} />
        <DescriptionItem label="Windows" value={formatInteger(run.window_count)} />
        <DescriptionItem label="Provenance version" value={run.provenance_version} />
        <DescriptionItem label="Evidence version" value={run.evidence_version} />
        <DescriptionItem label="Started at" value={formatTimestamp(run.started_at)} />
        <DescriptionItem label="Finished at" value={formatTimestamp(run.finished_at)} />
        <DescriptionItem label="Created at" value={formatTimestamp(run.created_at)} />
        <DescriptionItem label="Config checksum" value={<code className="mono-compact">{run.config_checksum}</code>} />
        <DescriptionItem label="Input checksum" value={<code className="mono-compact">{run.input_data_checksum}</code>} />
      </dl>
    </section>
  );
}

function EvidenceSection({ data }: { data: WalkForwardDetailResponse }) {
  if (data.evidence === null) {
    return (
      <section className="holdings-section" aria-labelledby="walk-forward-evidence-heading">
        <h2 id="walk-forward-evidence-heading">Aggregated evidence</h2>
        <p className="detail-note">
          Evidence is unavailable until this {data.run.status} run reaches a terminal state.
        </p>
        {data.run.error_message ? <FeedbackMessage variant="error">{data.run.error_message}</FeedbackMessage> : null}
      </section>
    );
  }

  const evidence = data.evidence;
  const metrics = Object.entries(evidence.metrics);
  return (
    <section className="holdings-section" aria-labelledby="walk-forward-evidence-heading">
      <h2 id="walk-forward-evidence-heading">Aggregated evidence</h2>
      <p className="detail-note">
        Evidence status uses a minimum-valid-count threshold; values below that threshold remain explicitly unavailable.
      </p>
      <div className="metric-card-grid">
        {metrics.map(([key, value]) => (
          <MetricCard key={key} label={metricLabels[key] ?? key} metric={value} />
        ))}
      </div>
      <dl className="compact-list">
        <DescriptionItem label="Positive-window rate" value={formatRate(evidence.positive_window_rate)} />
        <DescriptionItem label="Generalization gap" value={formatMetricSummary(evidence.generalization_gap)} />
      </dl>
      <BenchmarkEvidence data={data} />
      <ParameterStability evidence={evidence} />
      {evidence.tail_distribution ? <TailDistributionEvidence evidence={evidence} /> : null}
    </section>
  );
}

const TAIL_OWNER_LABELS: Record<string, string> = {
  strategy: "Strategy",
  equal_weight_monthly: "Equal-weight monthly",
  csi_300_buy_hold: "CSI 300 buy-and-hold"
};

const TAIL_METRIC_LABELS: Record<string, string> = {
  historical_var_95: "Historical VaR 95% (1D loss)",
  historical_cvar_95: "Historical CVaR 95% (1D loss)",
  return_skewness: "Skewness",
  return_excess_kurtosis: "Excess kurtosis (normal = 0)"
};

function TailDistributionEvidence({ evidence }: { evidence: PersistedWalkForwardEvidence }) {
  const tail = evidence.tail_distribution;
  if (tail === undefined) {
    return null;
  }
  return (
    <div className="walk-forward-subsection">
      <h3>One-day historical distribution risk (95%)</h3>
      <p className="detail-note">
        Aggregate values are descriptive statistics across independent per-window metric
        estimates; they are not VaR/CVaR or shape statistics calculated from a combined or
        stitched return distribution.
      </p>
      {Object.entries(tail.aggregates).map(([owner, aggregates]) => (
        <section aria-label={`Distribution aggregates for ${owner}`} className="benchmark-metrics" key={owner}>
          <h4>{TAIL_OWNER_LABELS[owner] ?? owner}</h4>
          <dl className="metric-card-grid">
            {Object.entries(aggregates).map(([metric, summary]) => (
              <MetricCard key={metric} label={TAIL_METRIC_LABELS[metric] ?? metric} metric={summary} />
            ))}
          </dl>
        </section>
      ))}
      <h4>Per-window evidence</h4>
      <div aria-label="Per-window distribution evidence" className="walk-forward-window-scroll" tabIndex={0}>
        <table className="holdings-table">
          <caption className="sr-only">
            Persisted one-day historical distribution evidence by window and owner
          </caption>
          <thead>
            <tr>
              <th scope="col">Window</th>
              <th scope="col">Owner</th>
              <th scope="col">VaR 95% (1D loss)</th>
              <th scope="col">CVaR 95% (1D loss)</th>
              <th scope="col">Skewness</th>
              <th scope="col">Excess kurtosis (normal = 0)</th>
              <th scope="col">Observations</th>
              <th scope="col">Tail (5%)</th>
              <th scope="col">Evidence</th>
            </tr>
          </thead>
          <tbody>
            {tail.per_window.flatMap((window) =>
              Object.entries(window.owners).map(([owner, ownerEvidence]) => (
                <tr key={`${window.ordinal}-${owner}`}>
                  <td>{window.ordinal}</td>
                  <td>{TAIL_OWNER_LABELS[owner] ?? owner}</td>
                  <td>{formatTailValue(ownerEvidence.historical_var_95)}</td>
                  <td>{formatTailValue(ownerEvidence.historical_cvar_95)}</td>
                  <td>{formatTailValue(ownerEvidence.return_skewness)}</td>
                  <td>{formatTailValue(ownerEvidence.return_excess_kurtosis)}</td>
                  <td>{ownerEvidence.observation_count}</td>
                  <td>{ownerEvidence.tail_observation_count}</td>
                  <td>{ownerEvidence.evidence_status}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatTailValue(value: number | null): string {
  return value === null ? "n/a" : value.toFixed(6);
}

function MetricCard({ label, metric }: { label: string; metric: WalkForwardMetricSummary }) {
  return (
    <div aria-label={`${label} summary`} className="metric-card">
      <span className="metric-card-label">{label}</span>
      <strong>Mean: {formatMetricValue(metric.mean)}</strong>
      <span>Median: {formatMetricValue(metric.median)}</span>
      <span>Range: {formatMetricValue(metric.min)} to {formatMetricValue(metric.max)}</span>
      <span>Population std: {formatMetricValue(metric.std)}</span>
      <span className="metric-card-meta">
        {metric.evidence_status} · {metric.valid_count}/{metric.window_count} valid
      </span>
    </div>
  );
}

function BenchmarkEvidence({ data }: { data: WalkForwardDetailResponse }) {
  if (data.evidence === null) {
    return null;
  }
  return (
    <div className="walk-forward-subsection">
      <h3>Benchmark evidence</h3>
      {Object.entries(data.evidence.benchmarks).map(([key, benchmark]) => (
        <section aria-label={`Benchmark ${key}`} className="benchmark-metrics" key={key}>
          <h4>{key}</h4>
          <dl className="compact-list">
            <DescriptionItem label="Total-return difference" value={formatMetricSummary(benchmark.total_return_difference)} />
            <DescriptionItem label="Annualized-return difference" value={formatMetricSummary(benchmark.annualized_return_difference)} />
            <DescriptionItem label="Tracking error" value={formatMetricSummary(benchmark.tracking_error)} />
            <DescriptionItem label="Information ratio" value={formatMetricSummary(benchmark.information_ratio)} />
            <DescriptionItem label="Outperformance rate" value={formatRate(benchmark.outperformance_rate)} />
            {key === "csi_300_buy_hold" &&
            benchmark.capm_alpha &&
            benchmark.capm_beta &&
            benchmark.capm_r_squared ? (
              <>
                <DescriptionItem label="CSI 300 ETF proxy Alpha (252D compounded)" value={formatMetricSummary(benchmark.capm_alpha)} />
                <DescriptionItem label="Beta (CSI 300 ETF proxy)" value={formatMetricSummary(benchmark.capm_beta)} />
                <DescriptionItem label="R-squared (CSI 300 ETF proxy)" value={formatMetricSummary(benchmark.capm_r_squared)} />
              </>
            ) : null}
            {benchmark.up_capture_ratio ? (
              <DescriptionItem label="Monthly Up Capture (selected months)" value={formatMetricSummary(benchmark.up_capture_ratio)} />
            ) : null}
            {benchmark.down_capture_ratio ? (
              <DescriptionItem label="Monthly Down Capture (selected months)" value={formatMetricSummary(benchmark.down_capture_ratio)} />
            ) : null}
          </dl>
        </section>
      ))}
    </div>
  );
}

function ParameterStability({ evidence }: { evidence: PersistedWalkForwardEvidence }) {
  return (
    <div className="walk-forward-subsection">
      <h3>Parameter stability</h3>
      {Object.entries(evidence.parameter_stability).map(([key, value]) => (
        <dl className="compact-list" key={key}>
          <DescriptionItem label={key} value={JSON.stringify(value.value_frequencies)} />
          <DescriptionItem label="Transition rate" value={formatDecimal(value.transition_rate === null ? null : String(value.transition_rate), 4)} />
          <DescriptionItem label="Transitions" value={`${formatInteger(value.transition_count)}/${formatInteger(value.comparison_count)}`} />
          <DescriptionItem label="Comparisons" value={formatInteger(value.comparison_count)} />
        </dl>
      ))}
    </div>
  );
}

function ProvenanceSection({ data }: { data: WalkForwardDetailResponse }) {
  const manifest = data.input_provenance.manifest;
  return (
    <section className="holdings-section" aria-labelledby="walk-forward-provenance-heading">
      <h2 id="walk-forward-provenance-heading">Configuration and input provenance</h2>
      <p className="detail-note">
        Configuration paths are display metadata; checksum identity uses validated effective content.
      </p>
      <dl className="compact-list">
        <DescriptionItem label="Config checksum" value={<code className="mono-compact">{data.configuration.config_checksum}</code>} />
        <DescriptionItem label="Input checksum" value={<code className="mono-compact">{data.input_provenance.input_data_checksum}</code>} />
        <DescriptionItem label="First loaded price date" value={manifestString(manifest, "first_loaded_price_date")} />
        <DescriptionItem label="Last loaded price date" value={manifestString(manifest, "last_loaded_price_date")} />
        <DescriptionItem label="Following-session sentinel" value={manifestString(manifest, "following_session")} />
      </dl>
      <div className="walk-forward-json-grid">
        <JsonBlock label="Walk-forward configuration" value={data.configuration.walk_forward} />
        <JsonBlock label="Base strategy configuration" value={data.configuration.base_strategy} />
        <JsonBlock label="Input manifest" value={manifest} />
      </div>
    </section>
  );
}

function JsonBlock({ label, value }: { label: string; value: object }) {
  return (
    <div>
      <h3>{label}</h3>
      <pre className="walk-forward-json">{JSON.stringify(value, null, 2)}</pre>
    </div>
  );
}

function WindowSection({ data }: { data: WalkForwardDetailResponse }) {
  if (data.windows.length === 0) {
    return (
      <section className="holdings-section" aria-labelledby="walk-forward-windows-heading">
        <h2 id="walk-forward-windows-heading">Window evidence</h2>
        <EmptyState>No OOS windows have been published for this {data.run.status} run.</EmptyState>
      </section>
    );
  }
  return (
    <section className="holdings-section" aria-labelledby="walk-forward-windows-heading">
      <h2 id="walk-forward-windows-heading">Window evidence</h2>
      <p className="detail-note">
        Each row is independent OOS evidence; the stitched capital path above compounds these
        segments under per-window reset semantics.
      </p>
      <div aria-label="Walk-forward window evidence" className="walk-forward-window-scroll" tabIndex={0}>
        <table className="holdings-table">
          <caption className="sr-only">Persisted train, candidate, and OOS evidence by window</caption>
          <thead>
            <tr>
              <th scope="col">Window</th>
              <th scope="col">Train / test</th>
              <th scope="col">Candidates</th>
              <th scope="col">Selected parameters</th>
              <th scope="col">Train Sharpe</th>
              <th scope="col">OOS strategy</th>
              <th scope="col">Fixed benchmarks</th>
            </tr>
          </thead>
          <tbody>
            {data.windows.map((window) => (
              <tr key={window.ordinal}>
                <td>{window.ordinal}</td>
                <td>{`${formatDate(window.train_start)} to ${formatDate(window.train_end)} / ${formatDate(window.test_start)} to ${formatDate(window.test_end)}`}</td>
                <td>
                  <div>Candidates: {formatInteger(window.candidate_count)}</div>
                  <div>Eligible: {formatInteger(window.eligible_count)}</div>
                  <div>Skipped: {formatInteger(window.skipped_count)}</div>
                  <div>{formatSkipReasons(window.skip_reason_counts)}</div>
                </td>
                <td><code className="mono-compact">{JSON.stringify(window.selected_parameters)}</code></td>
                <td>{formatNullableText(window.train_sharpe)}</td>
                <td>
                  <Link className="operation-link" to={`/backtests/${window.oos_backtest.run_id}`}>
                    Backtest #{window.oos_backtest.run_id}
                  </Link>
                  <div>{window.oos_version} · {window.oos_backtest.status}</div>
                  <OosStrategyMetrics backtest={window.oos_backtest} ordinal={window.ordinal} />
                </td>
                <td>
                  {window.oos_backtest.benchmarks.map((benchmark) => (
                    <BenchmarkMetrics benchmark={benchmark} key={benchmark.key} ordinal={window.ordinal} />
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function OosStrategyMetrics({
  backtest,
  ordinal
}: {
  backtest: WalkForwardDetailResponse["windows"][number]["oos_backtest"];
  ordinal: number;
}) {
  return (
    <div aria-label={`OOS strategy metrics for window ${ordinal}`} className="walk-forward-window-metrics">
      <div>Total return: {formatDecimal(backtest.total_return, 4)}</div>
      <div>Annualized return: {formatDecimal(backtest.annualized_return, 4)}</div>
      <div>Max drawdown: {formatDecimal(backtest.max_drawdown, 4)}</div>
      <div>Volatility: {formatDecimal(backtest.volatility, 4)}</div>
      <div>Sharpe: {formatDecimal(backtest.sharpe_ratio, 4)}</div>
      <div>Sortino: {formatDecimal(backtest.sortino_ratio, 4)}</div>
      <div>Calmar: {formatDecimal(backtest.calmar_ratio, 4)}</div>
      <DrawdownDuration value={backtest} />
    </div>
  );
}

function BenchmarkMetrics({
  benchmark,
  ordinal
}: {
  benchmark: WalkForwardBenchmark;
  ordinal: number;
}) {
  return (
    <section
      aria-label={`${benchmark.name} metrics for window ${ordinal}`}
      className="walk-forward-window-metrics"
    >
      <strong>{benchmark.name}</strong>
      <div>Total return: {formatDecimal(benchmark.total_return, 4)}</div>
      <div>Annualized return: {formatDecimal(benchmark.annualized_return, 4)}</div>
      <div>Max drawdown: {formatDecimal(benchmark.max_drawdown, 4)}</div>
      <div>Volatility: {formatDecimal(benchmark.volatility, 4)}</div>
      <div>Sharpe: {formatDecimal(benchmark.sharpe_ratio, 4)}</div>
      <div>Sortino: {formatDecimal(benchmark.sortino_ratio, 4)}</div>
      <div>Calmar: {formatDecimal(benchmark.calmar_ratio, 4)}</div>
      <DrawdownDuration value={benchmark} />
      <div>Total-return difference: {formatDecimal(benchmark.total_return_difference, 4)}</div>
      <div>Annualized-return difference: {formatDecimal(benchmark.annualized_return_difference, 4)}</div>
      <div>Tracking error: {formatDecimal(benchmark.tracking_error, 4)}</div>
      <div>Information ratio: {formatDecimal(benchmark.information_ratio, 4)}</div>
      {benchmark.key === "csi_300_buy_hold" ? (
        <>
          <div>CSI 300 ETF proxy Alpha (252D compounded): {formatDecimal(benchmark.capm_alpha, 4)}</div>
          <div>Beta (CSI 300 ETF proxy): {formatDecimal(benchmark.capm_beta, 4)}</div>
          <div>R-squared (CSI 300 ETF proxy): {formatDecimal(benchmark.capm_r_squared, 4)}</div>
          <div>CAPM observations (daily sessions): {formatNullableInteger(benchmark.capm_observation_count)}</div>
        </>
      ) : null}
      <div>Monthly Up Capture (selected months): {formatDecimal(benchmark.up_capture_ratio, 4)}</div>
      <div>Up selected months: {formatNullableInteger(benchmark.up_capture_observation_count)}</div>
      <div>Monthly Down Capture (selected months): {formatDecimal(benchmark.down_capture_ratio, 4)}</div>
      <div>Down selected months: {formatNullableInteger(benchmark.down_capture_observation_count)}</div>
    </section>
  );
}

type DrawdownDurationValue = Pick<
  WalkForwardBenchmark,
  | "longest_drawdown_duration_sessions"
  | "longest_drawdown_peak_date"
  | "longest_drawdown_trough_date"
  | "longest_drawdown_recovery_date"
>;

function DrawdownDuration({ value }: { value: DrawdownDurationValue }) {
  return (
    <>
      <div>Longest drawdown: {formatNullableInteger(value.longest_drawdown_duration_sessions)} sessions</div>
      <div>Peak: {formatDate(value.longest_drawdown_peak_date)}</div>
      <div>Trough: {formatDate(value.longest_drawdown_trough_date)}</div>
      <div>Recovery: {formatDrawdownRecovery(value)}</div>
    </>
  );
}

function formatMetricValue(value: number | null): string {
  return formatDecimal(value === null ? null : String(value), 4);
}

function formatMetricSummary(metric: WalkForwardMetricSummary): string {
  return `mean ${formatMetricValue(metric.mean)}; median ${formatMetricValue(metric.median)}; range ${formatMetricValue(metric.min)} to ${formatMetricValue(metric.max)}; std ${formatMetricValue(metric.std)}; ${metric.valid_count}/${metric.window_count} valid; ${metric.evidence_status}`;
}

function formatRate(rate: {
  value: number | null;
  numerator: number;
  denominator: number;
  window_count: number;
  valid_count: number;
  evidence_status: string;
}): string {
  const value = rate.value === null ? "n/a" : `${(rate.value * 100).toFixed(2)}%`;
  return `${value} (${rate.numerator}/${rate.denominator}); ${rate.valid_count}/${rate.window_count} valid; ${rate.evidence_status}`;
}

function formatSkipReasons(reasons: Record<string, number>): string {
  const entries = Object.entries(reasons);
  return entries.length === 0 ? "No skip reasons" : `Skip reasons: ${entries.map(([key, value]) => `${key}: ${value}`).join(", ")}`;
}

function manifestString(manifest: Record<string, unknown>, key: string): string {
  const value = manifest[key];
  return typeof value === "string" ? value : formatNullableText(undefined);
}

function formatDrawdownRecovery(
  backtest: DrawdownDurationValue
): string {
  if (backtest.longest_drawdown_recovery_date) {
    return formatDate(backtest.longest_drawdown_recovery_date);
  }

  return backtest.longest_drawdown_duration_sessions !== null &&
    backtest.longest_drawdown_duration_sessions > 0 &&
    backtest.longest_drawdown_peak_date !== null &&
    backtest.longest_drawdown_trough_date !== null
    ? "ongoing"
    : "n/a";
}
