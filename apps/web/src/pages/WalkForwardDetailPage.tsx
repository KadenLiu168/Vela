import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  type WalkForwardBenchmark,
  type WalkForwardDetailResponse,
  type WalkForwardMetricSummary,
  type WalkForwardOosBacktest,
  getWalkForwardDetail
} from "../api/client";
import { DescriptionItem, EmptyState, FeedbackMessage, ReadFailure } from "../components";
import { useDocumentTitle } from "../utils/documentTitle";
import { useResource, type ResourceState } from "../utils/useResource";
import { listReturnHref } from "../utils/listReturn";
import {
  formatDate,
  formatDecimal,
  formatInteger,
  formatNullableInteger,
  formatNullableText,
  formatTimestamp
} from "../utils/formatters";
import { StitchedOosSection } from "./StitchedOosSection";
import { WalkForwardOosSummarySection } from "./WalkForwardOosSummarySection";
import { WalkForwardRunHeaderSection } from "./WalkForwardRunHeaderSection";
import { formatDrawdownRecovery } from "./drawdownFormatters";
import { TableCells, TableHeader } from "./tablePrimitives";
import { TAIL_OWNER_LABELS } from "./walkForwardFormatters";

type WalkForwardDetailPageProps = {
  runId: string;
};

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

const WINDOW_METRIC_FIELDS = [
  ["Total return", "total_return"],
  ["Annualized return", "annualized_return"],
  ["Max drawdown", "max_drawdown"],
  ["Volatility", "volatility"],
  ["Sharpe", "sharpe_ratio"],
  ["Sortino", "sortino_ratio"],
  ["Calmar", "calmar_ratio"]
] as const satisfies ReadonlyArray<[
  string,
  keyof Pick<
    WalkForwardOosBacktest,
    "total_return" | "annualized_return" | "max_drawdown" | "volatility" | "sharpe_ratio" | "sortino_ratio" | "calmar_ratio"
  >
]>;

const BENCHMARK_METRIC_FIELDS = [
  ["Total-return difference", "total_return_difference"],
  ["Annualized-return difference", "annualized_return_difference"],
  ["Tracking error", "tracking_error"],
  ["Information ratio", "information_ratio"]
] as const;

const CAPM_FIELDS = [
  ["CSI 300 ETF proxy Alpha (252D compounded)", "capm_alpha"],
  ["Beta (CSI 300 ETF proxy)", "capm_beta"],
  ["R-squared (CSI 300 ETF proxy)", "capm_r_squared"]
] as const;

const CAPTURE_RATIO_FIELDS = [
  ["Monthly Up Capture (selected months)", "up_capture_ratio"],
  ["Monthly Down Capture (selected months)", "down_capture_ratio"]
] as const;

const CAPTURE_COUNT_FIELDS = [
  ["Up selected months", "up_capture_observation_count"],
  ["Down selected months", "down_capture_observation_count"]
] as const;

const TAIL_VALUE_FIELDS = [
  "historical_var_95",
  "historical_cvar_95",
  "return_skewness",
  "return_excess_kurtosis"
] as const;

const TAIL_TABLE_COLUMNS = [
  "Window",
  "Owner",
  "VaR 95% (1D loss)",
  "CVaR 95% (1D loss)",
  "Skewness",
  "Excess kurtosis (normal = 0)",
  "Observations",
  "Tail (5%)",
  "Evidence"
];

const WINDOW_TABLE_COLUMNS = [
  "Window",
  "Train / test",
  "Candidates",
  "Selected parameters",
  "Train Sharpe",
  "OOS strategy",
  "Fixed benchmarks"
]

/* Mono is applied per column by content semantics: windows, dates, counts,
 * parameters, and metrics render in Mono; owner labels, evidence statuses,
 * and the composite OOS/benchmark summaries stay Sans. */
const TAIL_CELL_CLASSNAMES = [
  "mono-compact",
  undefined,
  "mono-compact",
  "mono-compact",
  "mono-compact",
  "mono-compact",
  "mono-compact",
  "mono-compact",
  undefined
] as const;

const WINDOW_CELL_CLASSNAMES = [
  "mono-compact",
  "mono-compact",
  undefined,
  undefined,
  "mono-compact",
  undefined,
  undefined
] as const;

export function WalkForwardDetailPage({ runId }: WalkForwardDetailPageProps) {
  const location = useLocation();
  const backHref = listReturnHref(location.state, "/walk-forwards");
  const { state, reload } = useResource({
    hasNotFoundState: true,
    key: runId,
    load: () => getWalkForwardDetail(runId)
  });

  useDocumentTitle(`Walk-forward #${runId}`);

  return (
    <section className="page detail-page walk-forward-detail-page">
      <div className="page-heading">
        <p>Walk-forward research workspace</p>
        <h1>Walk-forward #{runId}</h1>
      </div>
      {renderDetail(state, runId, reload, backHref)}
    </section>
  );
}

function renderDetail(
  state: ResourceState<WalkForwardDetailResponse>,
  runId: string,
  retry: () => void,
  backHref: string
) {
  if (state.status === "loading") {
    return <FeedbackMessage variant="loading">Loading Walk-forward detail.</FeedbackMessage>;
  }

  if (state.status === "not-found") {
    return <EmptyState>Walk-forward run {runId} was not found.</EmptyState>;
  }

  if (state.status === "error") {
    return <ReadFailure error={state.error} label="Walk-forward detail" onRetry={retry} />;
  }

  const { data } = state;
  return (
    <article className="dashboard-panel">
      <WalkForwardRunHeaderSection backHref={backHref} run={data.run} />
      <WalkForwardOosSummarySection evidence={data.evidence} status={data.run.status} />
      <StitchedOosSection data={data} />
      <EvidenceSection data={data} />
      <WindowSection data={data} />
      <ProvenanceSection data={data} />
    </article>
  );
}

function EvidenceSection({ data }: { data: WalkForwardDetailResponse }) {
  if (data.evidence === null) {
    return (
      <section className="holdings-section" aria-labelledby="walk-forward-evidence-heading">
        <h2 id="walk-forward-evidence-heading">Aggregated evidence</h2>
        <p className="detail-note">
          No aggregated OOS metrics have been published for this {data.run.status} run yet.
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
        <DescriptionItem label="Positive-window rate" mono value={formatRate(evidence.positive_window_rate)} />
        <DescriptionItem label="Generalization gap" mono value={formatMetricSummary(evidence.generalization_gap)} />
      </dl>
      <BenchmarkEvidence data={data} />
      <ParameterStability evidence={evidence} />
      {evidence.tail_distribution ? <TailDistributionEvidence evidence={evidence} /> : null}
    </section>
  );
}

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
          <div className="metric-card-grid">
            {Object.entries(aggregates).map(([metric, summary]) => (
              <MetricCard key={metric} label={TAIL_METRIC_LABELS[metric] ?? metric} metric={summary} />
            ))}
          </div>
        </section>
      ))}
      <h4>Per-window evidence</h4>
      <div aria-label="Per-window distribution evidence" className="walk-forward-window-scroll" tabIndex={0}>
        <table className="holdings-table">
          <caption className="sr-only">
            Persisted one-day historical distribution evidence by window and owner
          </caption>
          <TableHeader columns={TAIL_TABLE_COLUMNS} />
          <tbody>
            {tail.per_window.flatMap((window) =>
              Object.entries(window.owners).map(([owner, ownerEvidence]) => (
                <tr key={`${window.ordinal}-${owner}`}>
                  <TableCells
                    classNames={TAIL_CELL_CLASSNAMES}
                    cells={[
                      window.ordinal,
                      TAIL_OWNER_LABELS[owner] ?? owner,
                      ...TAIL_VALUE_FIELDS.map((field) => formatTailValue(ownerEvidence[field])),
                      ownerEvidence.observation_count,
                      ownerEvidence.tail_observation_count,
                      ownerEvidence.evidence_status
                    ]}
                  />
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
      <strong>Mean: <span className="mono-compact">{formatMetricValue(metric.mean)}</span></strong>
      <span>Median: <span className="mono-compact">{formatMetricValue(metric.median)}</span></span>
      <span>
        Range: <span className="mono-compact">{formatMetricValue(metric.min)} to {formatMetricValue(metric.max)}</span>
      </span>
      <span>Population std: <span className="mono-compact">{formatMetricValue(metric.std)}</span></span>
      <span className="metric-card-meta">
        {metric.evidence_status} · <span className="mono-compact">{metric.valid_count}/{metric.window_count}</span> valid
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
            {BENCHMARK_METRIC_FIELDS.map(([label, field]) => (
              <DescriptionItem key={field} label={label} value={formatMetricSummary(benchmark[field])} mono />
            ))}
            <DescriptionItem label="Outperformance rate" mono value={formatRate(benchmark.outperformance_rate)} />
            {key === "csi_300_buy_hold" &&
            benchmark.capm_alpha &&
            benchmark.capm_beta &&
            benchmark.capm_r_squared ? (
              CAPM_FIELDS.map(([label, field]) => (
                <DescriptionItem key={field} label={label} value={formatMetricSummary(benchmark[field]!)} mono />
              ))
            ) : null}
            {CAPTURE_RATIO_FIELDS.map(([label, field]) =>
              benchmark[field] ? (
                <DescriptionItem key={field} label={label} value={formatMetricSummary(benchmark[field]!)} mono />
              ) : null
            )}
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
          {[
            [key, JSON.stringify(value.value_frequencies)],
            ["Transition rate", formatDecimal(value.transition_rate === null ? null : String(value.transition_rate), 4)],
            ["Transitions", `${formatInteger(value.transition_count)}/${formatInteger(value.comparison_count)}`],
            ["Comparisons", formatInteger(value.comparison_count)]
          ].map(([label, itemValue]) => (
            <DescriptionItem key={label} label={label} value={itemValue} mono />
          ))}
        </dl>
      ))}
    </div>
  );
}

function ProvenanceSection({ data }: { data: WalkForwardDetailResponse }) {
  const manifest = data.input_provenance.manifest;
  const isV2 = manifest.version === "wf_provenance_v2";
  const firstLoadedDate = isV2
    ? manifest.first_raw_price_date
    : manifest.first_loaded_price_date;
  const lastLoadedDate = isV2
    ? manifest.last_raw_price_date
    : manifest.last_loaded_price_date;
  const inputFields: [string, ReactNode][] = [
    ["Config checksum", <code className="mono-compact">{data.configuration.config_checksum}</code>],
    ["Input checksum", <code className="mono-compact">{data.input_provenance.input_data_checksum}</code>],
    ["First loaded price date", formatNullableText(firstLoadedDate ?? undefined)],
    ["Last loaded price date", formatNullableText(lastLoadedDate ?? undefined)],
    ["Following-session sentinel", formatNullableText(manifest.following_session ?? undefined)]
  ];
  return (
    <section className="holdings-section" aria-labelledby="walk-forward-provenance-heading">
      <h2 id="walk-forward-provenance-heading">Configuration and input provenance</h2>
      <div className="walk-forward-subsection">
        <h3>Execution</h3>
        <dl className="compact-list">
          {[
            ["Provenance version", data.run.provenance_version],
            ["Evidence version", data.run.evidence_version],
            ["Started at", formatTimestamp(data.run.started_at)],
            ["Finished at", formatTimestamp(data.run.finished_at)],
            ["Created at", formatTimestamp(data.run.created_at)]
          ].map(([label, value]) => (
            <DescriptionItem key={label} label={label} value={value} mono />
          ))}
        </dl>
      </div>
      <p className="detail-note">
        Configuration paths are display metadata; checksum identity uses validated effective content.
      </p>
      <dl className="compact-list">
        {inputFields.map(([label, value]) => (
          <DescriptionItem key={label} label={label} value={value} mono />
        ))}
        {isV2 ? (
          <>
            <DescriptionItem label="Resolution policy" mono value={manifest.resolution_policy_version} />
            <DescriptionItem label="Raw / derived sessions" mono value={`${manifest.raw_price_row_count} / ${manifest.derived_session_count}`} />
            {manifest.active_etfs.map((etf) => (
              <DescriptionItem
                key={`${etf.exchange}:${etf.symbol}`}
                label={`${etf.exchange}:${etf.symbol} listing date`}
                mono value={etf.listing_date}
              />
            ))}
          </>
        ) : null}
      </dl>
      {isV2 ? (
        <div aria-label="Non-trading evidence">
          {manifest.active_etfs.flatMap((etf) => etf.status_evidence.map((evidence) => (
            <article
              className="detail-note"
              key={`${etf.etf_id}-${evidence.trade_date}-${evidence.source_uri}`}
              aria-label={`Derived non-trading valuation for ${etf.exchange}:${etf.symbol} on ${evidence.trade_date}`}
            >
              <strong>Derived non-trading valuation</strong>
              <p>{evidence.trade_date}: {evidence.status}; {evidence.reason}</p>
              <p>Carried adjusted value: {evidence.carried_adjusted_value}</p>
              <p>Carried from: {evidence.carry_from_trade_date}</p>
              <a href={evidence.source_uri} target="_blank" rel="noreferrer">Source evidence</a>
            </article>
          )))}
        </div>
      ) : null}
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
      {/* The JSON block scrolls internally; it needs a keyboard focus stop so
       * screen-reader and keyboard users can reach its content. */}
      <pre className="walk-forward-json" tabIndex={0}>{JSON.stringify(value, null, 2)}</pre>
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
          <TableHeader columns={WINDOW_TABLE_COLUMNS} />
          <tbody>
            {data.windows.map((window) => {
              const candidateSummary = (
                <>
                  {([
                    ["Candidates", window.candidate_count],
                    ["Eligible", window.eligible_count],
                    ["Skipped", window.skipped_count]
                  ] as [string, number][]).map(([label, count]) => (
                    <div key={label}>
                      {label}: <span className="mono-compact">{formatInteger(count)}</span>
                    </div>
                  ))}
                  <div>{formatSkipReasons(window.skip_reason_counts)}</div>
                </>
              );
              const oosSummary = (
                <>
                  <Link className="operation-link" to={`/backtests/${window.oos_backtest.run_id}`}>
                    Backtest #{window.oos_backtest.run_id}
                  </Link>
                  <div>{window.oos_version} · {window.oos_backtest.status}</div>
                  <OosStrategyMetrics backtest={window.oos_backtest} ordinal={window.ordinal} />
                </>
              );
              const benchmarkSummary = window.oos_backtest.benchmarks.map((benchmark) => (
                <BenchmarkMetrics benchmark={benchmark} key={benchmark.key} ordinal={window.ordinal} />
              ));
              return (
                <tr key={window.ordinal}>
                  <TableCells
                    classNames={WINDOW_CELL_CLASSNAMES}
                    cells={[
                      window.ordinal,
                      `${formatDate(window.train_start)} to ${formatDate(window.train_end)} / ${formatDate(window.test_start)} to ${formatDate(window.test_end)}`,
                      candidateSummary,
                      <code className="mono-compact">{JSON.stringify(window.selected_parameters)}</code>,
                      formatNullableText(window.train_sharpe),
                      oosSummary,
                      benchmarkSummary
                    ]}
                  />
                </tr>
              );
            })}
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
      <WindowMetricRows value={backtest} />
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
      <WindowMetricRows value={benchmark} />
      <DrawdownDuration value={benchmark} />
      {BENCHMARK_METRIC_FIELDS.map(([label, key]) => (
        <div key={key}>
          {label}: <span className="mono-compact">{formatDecimal(benchmark[key], 4)}</span>
        </div>
      ))}
      {benchmark.key === "csi_300_buy_hold" ? (
        <>
          {CAPM_FIELDS.map(([label, key]) => (
            <div key={key}>
              {label}: <span className="mono-compact">{formatDecimal(benchmark[key], 4)}</span>
            </div>
          ))}
          <div>
            CAPM observations (daily sessions):{" "}
            <span className="mono-compact">{formatNullableInteger(benchmark.capm_observation_count)}</span>
          </div>
        </>
      ) : null}
      {CAPTURE_RATIO_FIELDS.map(([label, key]) => (
        <div key={key}>
          {label}: <span className="mono-compact">{formatDecimal(benchmark[key], 4)}</span>
        </div>
      ))}
      {CAPTURE_COUNT_FIELDS.map(([label, key]) => (
        <div key={key}>
          {label}: <span className="mono-compact">{formatNullableInteger(benchmark[key])}</span>
        </div>
      ))}
    </section>
  );
}

function WindowMetricRows({ value }: { value: Pick<WalkForwardOosBacktest, (typeof WINDOW_METRIC_FIELDS)[number][1]> }) {
  return WINDOW_METRIC_FIELDS.map(([label, key]) => (
    <div key={key}>
      {label}: <span className="mono-compact">{formatDecimal(value[key], 4)}</span>
    </div>
  ));
}

type DrawdownDurationValue = Pick<
  WalkForwardBenchmark,
  | "longest_drawdown_duration_sessions"
  | "longest_drawdown_peak_date"
  | "longest_drawdown_trough_date"
  | "longest_drawdown_recovery_date"
>;

function DrawdownDuration({ value }: { value: DrawdownDurationValue }) {
  const recovery = formatDrawdownRecovery(value);
  const recoveryIsDate = recovery !== "ongoing" && recovery !== "n/a";
  return (
    <>
      <div>
        Longest drawdown: <span className="mono-compact">{formatNullableInteger(value.longest_drawdown_duration_sessions)}</span>{" "}
        sessions
      </div>
      <div>
        Peak: <span className="mono-compact">{formatDate(value.longest_drawdown_peak_date)}</span>
      </div>
      <div>
        Trough: <span className="mono-compact">{formatDate(value.longest_drawdown_trough_date)}</span>
      </div>
      <div>
        Recovery: <span className={recoveryIsDate ? "mono-compact" : undefined}>{recovery}</span>
      </div>
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

function formatSkipReasons(reasons: Record<string, number>): ReactNode {
  const entries = Object.entries(reasons);
  if (entries.length === 0) {
    return "No skip reasons";
  }
  return (
    <>
      Skip reasons: {entries.map(([key, value], index) => (
        <span key={key}>
          {index > 0 ? ", " : ""}
          {key}: <span className="mono-compact">{formatInteger(value)}</span>
        </span>
      ))}
    </>
  );
}
