import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  ApiClientError,
  type BacktestBenchmark,
  type BacktestDetailResponse,
  type BacktestDetailMetrics,
  type BacktestSignalSummary,
  getBacktestDetail,
  listBacktestSignals
} from "../api/client";
import { DescriptionItem, EmptyState, FeedbackMessage, Pagination } from "../components";
import {
  formatDate,
  formatDecimal,
  formatInteger,
  formatNullableInteger,
  formatNullableText,
  formatNetValue,
  formatRatioAsPercent,
  formatTimestamp
} from "../utils/formatters";
import { formatEquityCurvePoint, formatParameterSummary } from "./backtestFormatters";
import {
  bestCellIndexes,
  type ComparisonRow
} from "./comparisonMatrix";
import { DistributionRiskSection } from "./DistributionRiskSection";
import { ReturnStabilitySection } from "./ReturnStabilitySection";
import {
  computeEquityCurveGeometry,
  computeMultiEquityCurveGeometry,
  computeSeriesEndLabels,
  EQUITY_CURVE_CHART,
  normalizeEquityCurvePoints,
  type EquityCurveChartSeries
} from "./equityCurveChart";
import { seriesColor } from "./seriesColor";

type BacktestDetailPageProps = {
  backtestId: string;
};

type BacktestDetailState =
  | { status: "loading"; data?: never; error?: never; backtestId?: never }
  | { status: "ready"; data: BacktestDetailResponse; error?: never; backtestId: string }
  | { status: "not-found"; data?: never; error?: never; backtestId: string }
  | { status: "error"; data?: never; error: string; backtestId: string };

type SignalsState =
  | { status: "idle"; data?: never; error?: never; offset?: never }
  | { status: "loading"; data?: never; error?: never; offset: number }
  | { status: "ready"; data: BacktestSignalSummary[]; error?: never; offset: number }
  | { status: "error"; data?: never; error: string; offset: number };

const PAGE_SIZE = 20;

export function BacktestDetailPage({ backtestId }: BacktestDetailPageProps) {
  return <BacktestDetailPageForId backtestId={backtestId} key={backtestId} />;
}

function BacktestDetailPageForId({ backtestId }: BacktestDetailPageProps) {
  const [backtestState, setBacktestState] = useState<BacktestDetailState>({
    status: "loading"
  });
  const [activeTab, setActiveTab] = useState<"overview" | "signals">("overview");
  const [signalOffset, setSignalOffset] = useState(0);
  const [signalsState, setSignalsState] = useState<SignalsState>({ status: "idle" });
  const signalRequestKey = useRef(0);
  const loadedSignalOffset = useRef<number | null>(null);

  useEffect(() => {
    let isCurrent = true;

    getBacktestDetail(backtestId)
      .then((data) => {
        if (isCurrent) {
          setBacktestState({ status: "ready", data, backtestId });
        }
      })
      .catch((error: unknown) => {
        if (!isCurrent) {
          return;
        }

        if (error instanceof ApiClientError && error.status === 404) {
          setBacktestState({ status: "not-found", backtestId });
          return;
        }

        setBacktestState({
          status: "error",
          error: error instanceof ApiClientError ? error.kind : "unavailable",
          backtestId
        });
      });

    return () => {
      isCurrent = false;
    };
  }, [backtestId]);

  useEffect(() => {
    if (activeTab !== "signals" || backtestState.status !== "ready" || backtestState.backtestId !== backtestId || backtestState.data.signal_count === 0) {
      return;
    }
    if (loadedSignalOffset.current === signalOffset) {
      return;
    }
    const requestKey = ++signalRequestKey.current;
    listBacktestSignals(backtestId, PAGE_SIZE, signalOffset)
      .then((data) => {
        if (signalRequestKey.current === requestKey) {
          loadedSignalOffset.current = signalOffset;
          setSignalsState({ status: "ready", data: data.signals, offset: signalOffset });
        }
      })
      .catch((error: unknown) => {
        if (signalRequestKey.current === requestKey) {
          setSignalsState({
            status: "error",
            error: error instanceof ApiClientError ? error.kind : "unavailable",
            offset: signalOffset
          });
        }
      });
  }, [activeTab, backtestId, backtestState, signalOffset]);

  return (
    <section className="page detail-page">
      <div className="page-heading">
        <p>Backtest research workspace</p>
        <h1>Backtest Detail</h1>
      </div>
      {renderBacktestDetail(
        getBacktestDetailState(backtestState, backtestId),
        backtestId,
        activeTab,
        (tab) => {
          setActiveTab(tab);
          if (tab === "signals" && signalsState.status === "idle" && backtestState.status === "ready" && backtestState.data.signal_count > 0) {
            setSignalsState({ status: "loading", offset: signalOffset });
          }
        },
        signalOffset,
        (offset) => {
          setSignalOffset(offset);
          setSignalsState({ status: "loading", offset });
        },
        signalsState
      )}
    </section>
  );
}

function getBacktestDetailState(state: BacktestDetailState, backtestId: string): BacktestDetailState {
  return state.status === "loading" || state.backtestId === backtestId ? state : { status: "loading" };
}

function renderBacktestDetail(
  backtestState: BacktestDetailState,
  backtestId: string,
  activeTab: "overview" | "signals",
  setActiveTab: (tab: "overview" | "signals") => void,
  signalOffset: number,
  setSignalOffset: (offset: number) => void,
  signalsState: SignalsState
) {
  if (backtestState.status === "loading") {
    return <FeedbackMessage variant="loading">Loading backtest detail.</FeedbackMessage>;
  }

  if (backtestState.status === "not-found") {
    return <EmptyState>Backtest run {backtestId} was not found.</EmptyState>;
  }

  if (backtestState.status === "error") {
    return (
      <FeedbackMessage className="dashboard-alert" variant="error">
        Backtest detail API unavailable: {backtestState.error}
      </FeedbackMessage>
    );
  }

  const { metrics, run } = backtestState.data;
  const signalCount = backtestState.data.signal_count;
  const selectTab = setActiveTab;
  const onTabKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    const tab =
      event.key === "Home"
        ? "overview"
        : event.key === "End"
          ? "signals"
          : event.key === "ArrowLeft" || event.key === "ArrowRight"
            ? activeTab === "overview"
              ? "signals"
              : "overview"
            : undefined;
    if (tab === undefined) return;
    event.preventDefault();
    selectTab(tab);
    document.getElementById(`backtest-${tab}-tab`)?.focus();
  };

  return (
    <article className="dashboard-panel">
      <strong className="panel-primary">Backtest #{run.run_id}</strong>
      <div aria-label="Backtest detail sections" className="backtest-tabs" role="tablist">
        <button aria-controls="backtest-overview-panel" aria-selected={activeTab === "overview"} className="backtest-tab" id="backtest-overview-tab" onClick={() => selectTab("overview")} onKeyDown={onTabKeyDown} role="tab" tabIndex={activeTab === "overview" ? 0 : -1} type="button">Overview</button>
        <button aria-controls="backtest-signals-panel" aria-selected={activeTab === "signals"} className="backtest-tab" id="backtest-signals-tab" onClick={() => selectTab("signals")} onKeyDown={onTabKeyDown} role="tab" tabIndex={activeTab === "signals" ? 0 : -1} type="button">Signals ({signalCount})</button>
      </div>
      {activeTab === "overview" ? (
      <div aria-labelledby="backtest-overview-tab" id="backtest-overview-panel" role="tabpanel">
      <dl className="compact-list">
        <DescriptionItem label="Strategy" value={run.strategy_id} />
        <DescriptionItem label="Config version" value={run.config_version} />
        <DescriptionItem label="Date range" value={`${formatDate(run.start_date)} to ${formatDate(run.end_date)}`} />
        <DescriptionItem label="Status" value={run.status} />
        <DescriptionItem label="Started at" value={formatTimestamp(run.started_at)} />
        <DescriptionItem label="Finished at" value={formatTimestamp(run.finished_at)} />
        <DescriptionItem label="Error message" value={formatNullableText(run.error_message)} />
      </dl>
      <section className="holdings-section" aria-labelledby="backtest-metrics-heading">
        <h3 id="backtest-metrics-heading">Metrics</h3>
        <div aria-label="Strategy headline metrics" className="backtest-hero-grid">
          <MetricCard label="Total return" value={formatRatioAsPercent(metrics.total_return)} />
          <MetricCard label="CAGR (calendar-time)" value={formatRatioAsPercent(metrics.annualized_return)} />
          <MetricCard label="Sharpe (daily returns, 252D)" value={formatDecimal(metrics.sharpe_ratio, 2, false)} />
          <MetricCard label="Max drawdown" value={formatRatioAsPercent(metrics.max_drawdown)} />
        </div>
        {(backtestState.data.benchmarks ?? []).length === 0 ? (
          <p className="detail-note">No benchmark comparison is available for this run.</p>
        ) : (
          <ComparisonMatrix
            metrics={metrics}
            benchmarks={backtestState.data.benchmarks}
          />
        )}
        <DistributionRiskSection fields={metrics} />
        {(backtestState.data.benchmarks ?? []).map((benchmark) => (
          <DistributionRiskSection
            fields={benchmark}
            key={benchmark.key}
            ownerName={benchmark.name}
          />
        ))}
        <ReturnStabilitySection stability={backtestState.data.return_stability} />
        {backtestState.data.benchmarks?.find((benchmark) => benchmark.key === "csi_300_buy_hold") ? (
          <CapmSection benchmark={backtestState.data.benchmarks.find((benchmark) => benchmark.key === "csi_300_buy_hold")!} />
        ) : null}
      </section>
      <section className="holdings-section" aria-labelledby="backtest-equity-curve-heading">
        <h3 id="backtest-equity-curve-heading">Equity curve</h3>
        <EquityCurveChart
          points={backtestState.data.equity_curve}
          benchmarks={backtestState.data.benchmarks ?? []}
        />
      </section>
      <section className="holdings-section" aria-labelledby="backtest-parameters-heading">
        <h3 id="backtest-parameters-heading">Parameters</h3>
        <pre className="parameter-summary">{formatParameterSummary(run.parameters_json)}</pre>
      </section>
      </div>
      ) : (
        <SignalsPanel count={signalCount} offset={signalOffset} setOffset={setSignalOffset} state={signalsState} />
      )}
    </article>
  );
}

function SignalsPanel({ count, offset, setOffset, state }: { count: number; offset: number; setOffset: (offset: number) => void; state: SignalsState }) {
  return <section aria-labelledby="backtest-signals-tab" className="holdings-section" id="backtest-signals-panel" role="tabpanel">
    {count === 0 ? <EmptyState>No signals are linked to this backtest.</EmptyState> : state.status === "loading" || state.status === "idle" ? <FeedbackMessage variant="loading">Loading backtest signals.</FeedbackMessage> : state.status === "error" ? <FeedbackMessage variant="error">Backtest signals API unavailable: {state.error}</FeedbackMessage> : <><div className="holdings-table-wrap"><table className="holdings-table"><thead><tr><th scope="col">Signal #</th><th scope="col">Signal date</th><th scope="col">Result</th><th scope="col">Action</th></tr></thead><tbody>{state.data.map((signal) => <tr key={signal.signal_id}><td>{signal.signal_id}</td><td>{formatDate(signal.signal_date)}</td><td>{formatNullableText(signal.result)}</td><td><Link className="operation-link" to={`/signals/${signal.signal_id}`}>Signal #{signal.signal_id}</Link></td></tr>)}</tbody></table></div><Pagination itemCount={state.data.length} offset={offset} onOffsetChange={setOffset} pageSize={PAGE_SIZE} totalCount={count} /></>}
  </section>;
}

function EquityCurveChart({
  points,
  benchmarks
}: {
  points: BacktestDetailResponse["equity_curve"];
  benchmarks: BacktestDetailResponse["benchmarks"];
}) {
  const chartPoints = normalizeEquityCurvePoints(points);
  const chartSeries: EquityCurveChartSeries[] = [
    { key: "strategy", name: "Strategy", points: chartPoints },
    ...benchmarks.map((benchmark) => ({
      key: benchmark.key,
      name: benchmark.name,
      points: normalizeEquityCurvePoints(benchmark.equity_curve)
    }))
  ].filter((series) => series.points.length > 0);

  if (chartPoints.length === 0) {
    return <EmptyState>No valid equity curve points are available for this run.</EmptyState>;
  }

  if (chartPoints.length === 1) {
    const point = chartPoints[0];

    return (
      <div className="equity-curve-single-point">
        <EmptyState>Only one equity curve point is available.</EmptyState>
        <dl className="equity-curve-summary">
          <DescriptionItem label="Point count" value={formatInteger(1)} />
          <DescriptionItem label="Trade date" value={formatDate(point.tradeDate)} />
          <DescriptionItem label="Net value" value={formatNetValue(point.netValue)} />
        </dl>
      </div>
    );
  }

  const { maxNetValue, minNetValue, series, dateTicks, valueTicks } = computeMultiEquityCurveGeometry(chartSeries);
  const legacyGeometry = series.length === 1 ? computeEquityCurveGeometry(chartPoints) : null;
  const endLabels = computeSeriesEndLabels(series);
  const firstPoint = chartPoints[0];
  const lastPoint = chartPoints[chartPoints.length - 1];
  return (
    <div className="equity-curve-card">
      <svg
        aria-labelledby="equity-curve-chart-title"
        className="equity-curve-chart"
        role="img"
        viewBox={`0 0 ${EQUITY_CURVE_CHART.width} ${EQUITY_CURVE_CHART.height}`}
      >
        <title id="equity-curve-chart-title">Equity curve net value chart</title>
        <line
          className="equity-curve-grid-line"
          x1={EQUITY_CURVE_CHART.paddingLeft}
          x2={EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingRight}
          y1={EQUITY_CURVE_CHART.paddingTop}
          y2={EQUITY_CURVE_CHART.paddingTop}
        />
        <line
          className="equity-curve-grid-line"
          x1={EQUITY_CURVE_CHART.paddingLeft}
          x2={EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingRight}
          y1={EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom}
          y2={EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom}
        />
        <line
          aria-hidden="true"
          className="equity-curve-axis"
          x1={EQUITY_CURVE_CHART.paddingLeft}
          x2={EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingRight}
          y1={EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom}
          y2={EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom}
        />
        <line
          aria-hidden="true"
          className="equity-curve-axis"
          x1={EQUITY_CURVE_CHART.paddingLeft}
          x2={EQUITY_CURVE_CHART.paddingLeft}
          y1={EQUITY_CURVE_CHART.paddingTop}
          y2={EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom}
        />
        {dateTicks.map((tick) => (
          <text
            className="equity-curve-axis-tick"
            data-testid="equity-curve-x-tick"
            key={tick.value}
            textAnchor="middle"
            x={tick.x}
            y={EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom + 16}
          >
            {tick.value}
          </text>
        ))}
        {valueTicks.map((tick) => (
          <text
            className="equity-curve-axis-tick"
            data-testid="equity-curve-y-tick"
            key={tick.value}
            textAnchor="end"
            x={EQUITY_CURVE_CHART.paddingLeft - 8}
            y={tick.y + 4}
          >
            {tick.value.toFixed(2)}
          </text>
        ))}
        {series.map((item) => (
          <path
            className="equity-curve-line"
            d={item.linePath}
            data-testid={series.length === 1 ? "equity-curve-line" : `equity-curve-line-${item.key}`}
            key={item.key}
            stroke={seriesColor(item.key)}
          />
        ))}
        {endLabels.map((label) => (
          <text
            className="equity-curve-end-label"
            data-testid={`equity-curve-end-label-${label.key}`}
            fill={seriesColor(label.key)}
            key={label.key}
            textAnchor="end"
            x={label.x}
            y={label.y}
          >
            {label.name}
          </text>
        ))}
        {legacyGeometry?.highlightCoordinates.map((coordinate) => (
          <circle
            className="equity-curve-highlight"
            cx={coordinate.x}
            cy={coordinate.y}
            data-testid="equity-curve-highlight"
            key={coordinate.index}
            r="4"
          />
        ))}
      </svg>
      <ul aria-label="Equity curve legend" className="equity-curve-legend">
        {series.map((item) => (
          <li className="equity-curve-legend-item" key={item.key}>
            <span
              aria-hidden="true"
              className="equity-curve-swatch"
              data-testid={`equity-curve-swatch-${item.key}`}
              style={{ backgroundColor: seriesColor(item.key) }}
            />
            {item.name}
          </li>
        ))}
      </ul>
      <dl className="equity-curve-summary">
        <DescriptionItem label="Point count" value={formatInteger(chartPoints.length)} />
        <DescriptionItem label="Start point" value={formatEquityCurvePoint(firstPoint)} />
        <DescriptionItem label="End point" value={formatEquityCurvePoint(lastPoint)} />
        <DescriptionItem label="Min net value" value={formatNetValue(minNetValue)} />
        <DescriptionItem label="Max net value" value={formatNetValue(maxNetValue)} />
      </dl>
    </div>
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

function toComparableNumber(value: string | null): number | null {
  if (value === null) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Side-by-side strategy versus benchmark matrix (方案 A): absolute rows for
 *  every entity plus strategy-relative rows whose Strategy cell stays n/a. */
function ComparisonMatrix({
  metrics,
  benchmarks
}: {
  metrics: BacktestDetailMetrics;
  benchmarks: BacktestBenchmark[];
}) {
  const entities: BacktestDetailMetrics[] = [metrics, ...benchmarks];
  const toNumber = toComparableNumber;

  const absoluteRows: ComparisonRow[] = [
    {
      key: "total_return",
      label: "Total return",
      cells: entities.map((entity) => formatRatioAsPercent(entity.total_return)),
      numeric: entities.map((entity) => toNumber(entity.total_return)),
      direction: "higher",
      rankable: true
    },
    {
      key: "annualized_return",
      label: "CAGR (calendar-time)",
      cells: entities.map((entity) => formatRatioAsPercent(entity.annualized_return)),
      numeric: entities.map((entity) => toNumber(entity.annualized_return)),
      direction: "higher",
      rankable: true
    },
    {
      key: "max_drawdown",
      label: "Max drawdown",
      cells: entities.map((entity) => formatRatioAsPercent(entity.max_drawdown)),
      numeric: entities.map((entity) => toNumber(entity.max_drawdown)),
      direction: "closest-to-zero",
      rankable: true
    },
    {
      key: "volatility",
      label: "Annualized volatility (252D)",
      cells: entities.map((entity) => formatRatioAsPercent(entity.volatility)),
      numeric: entities.map((entity) => toNumber(entity.volatility)),
      direction: "lower",
      rankable: true
    },
    {
      key: "sharpe_ratio",
      label: "Sharpe (daily returns, 252D)",
      cells: entities.map((entity) => formatDecimal(entity.sharpe_ratio, 2, false)),
      numeric: entities.map((entity) => toNumber(entity.sharpe_ratio)),
      direction: "higher",
      rankable: true
    },
    {
      key: "sortino_ratio",
      label: "Sortino (rf MAR, 252D)",
      cells: entities.map((entity) => formatDecimal(entity.sortino_ratio, 6, false)),
      numeric: entities.map((entity) => toNumber(entity.sortino_ratio)),
      direction: "higher",
      rankable: true
    },
    {
      key: "calmar_ratio",
      label: "Calmar (calendar CAGR / |MaxDD|)",
      cells: entities.map((entity) => formatDecimal(entity.calmar_ratio, 6, false)),
      numeric: entities.map((entity) => toNumber(entity.calmar_ratio)),
      direction: "higher",
      rankable: true
    },
    {
      key: "longest_drawdown_duration_sessions",
      label: "Longest drawdown duration (official sessions)",
      cells: entities.map((entity) => formatNullableInteger(entity.longest_drawdown_duration_sessions)),
      numeric: entities.map((entity) => entity.longest_drawdown_duration_sessions),
      direction: "lower",
      rankable: true
    },
    {
      key: "longest_drawdown_peak_date",
      label: "Longest drawdown peak date",
      cells: entities.map((entity) => formatDate(entity.longest_drawdown_peak_date))
    },
    {
      key: "longest_drawdown_trough_date",
      label: "Longest drawdown trough date",
      cells: entities.map((entity) => formatDate(entity.longest_drawdown_trough_date))
    },
    {
      key: "longest_drawdown_recovery",
      label: "Longest drawdown recovery",
      cells: entities.map((entity) => formatDrawdownRecovery(entity))
    }
  ];

  const relativeRows: ComparisonRow[] = [
    {
      key: "tracking_error",
      label: "Tracking error (252D)",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatDecimal(benchmark.tracking_error, 6, false))]
    },
    {
      key: "information_ratio",
      label: "Information ratio (252D)",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatDecimal(benchmark.information_ratio, 6, false))]
    },
    {
      key: "up_capture_ratio",
      label: "Monthly Up Capture (selected months)",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatRatioAsPercent(benchmark.up_capture_ratio))]
    },
    {
      key: "up_count",
      label: "Up selected months",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatNullableInteger(benchmark.up_capture_observation_count))]
    },
    {
      key: "down_capture_ratio",
      label: "Monthly Down Capture (selected months)",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatRatioAsPercent(benchmark.down_capture_ratio))]
    },
    {
      key: "down_count",
      label: "Down selected months",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatNullableInteger(benchmark.down_capture_observation_count))]
    },
    {
      key: "total_return_difference",
      label: "Strategy total return difference",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatRatioAsPercent(benchmark.total_return_difference))]
    },
    {
      key: "annualized_return_difference",
      label: "Strategy CAGR difference",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatRatioAsPercent(benchmark.annualized_return_difference))]
    }
  ];

  return (
    <div
      aria-label="Strategy vs benchmark comparison matrix region"
      className="comparison-matrix-wrap"
      tabIndex={0}
    >
      <table className="comparison-matrix holdings-table">
        <caption className="sr-only">Strategy vs benchmark comparison matrix</caption>
        <thead>
          <tr>
            <th scope="col">Metric</th>
            <th scope="col">Strategy</th>
            {benchmarks.map((benchmark) => (
              <th scope="col" key={benchmark.key}>
                {benchmark.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody aria-label="Absolute metrics">
          {absoluteRows.map((row) => (
            <MatrixRow key={row.key} row={row} />
          ))}
        </tbody>
        <tbody aria-label="Strategy-relative metrics">
          {relativeRows.map((row) => (
            <MatrixRow key={row.key} row={row} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MatrixRow({ row }: { row: ComparisonRow }) {
  const bestIndexes = new Set(bestCellIndexes(row));
  return (
    <tr data-testid={`comparison-row-${row.key}`}>
      <th scope="row">{row.label}</th>
      {row.cells.map((cell, index) => (
        <td className={bestIndexes.has(index) ? "comparison-best" : undefined} key={index}>
          {cell}
          {bestIndexes.has(index) ? <span className="comparison-best-badge">Best</span> : null}
        </td>
      ))}
    </tr>
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

function formatDrawdownRecovery(
  metrics: Pick<BacktestDetailMetrics, "longest_drawdown_duration_sessions" | "longest_drawdown_peak_date" | "longest_drawdown_trough_date" | "longest_drawdown_recovery_date">
): string {
  if (metrics.longest_drawdown_recovery_date) {
    return formatDate(metrics.longest_drawdown_recovery_date);
  }

  return metrics.longest_drawdown_duration_sessions !== null &&
    metrics.longest_drawdown_duration_sessions > 0 &&
    metrics.longest_drawdown_peak_date !== null &&
    metrics.longest_drawdown_trough_date !== null
    ? "ongoing"
    : "n/a";
}
