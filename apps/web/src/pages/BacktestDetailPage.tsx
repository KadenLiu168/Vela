import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  type BacktestDetailResponse,
  type BacktestSignalSummary,
  getBacktestDetail,
  listBacktestSignals
} from "../api/client";
import { DescriptionItem, EmptyState, FeedbackMessage, Pagination, ReadFailure } from "../components";
import { useDocumentTitle } from "../utils/documentTitle";
import { useResource, type ResourceState } from "../utils/useResource";
import { listReturnHref } from "../utils/listReturn";
import {
  formatDate,
  formatInteger,
  formatNullableText,
  formatNetValue
} from "../utils/formatters";
import { formatEquityCurvePoint } from "./backtestFormatters";
import { BenchmarkComparisonSection } from "./BenchmarkComparisonSection";
import { DecisionSummarySection } from "./DecisionSummarySection";
import { DeepAnalysisSection } from "./DeepAnalysisSection";
import { ExperimentConfigSection } from "./ExperimentConfigSection";
import {
  computeEquityCurveGeometry,
  computeMultiEquityCurveGeometry,
  normalizeEquityCurvePoints,
  type EquityCurveChartSeries
} from "./equityCurveChart";
import { EquityCurvePlot } from "./EquityCurvePlot";
import { ScrollableTableWrap, TableCells, TableHeader } from "./tablePrimitives";

type BacktestDetailPageProps = {
  backtestId: string;
};

type SignalsState =
  | { status: "idle"; data?: never; error?: never; offset?: never }
  | { status: "loading"; data?: never; error?: never; offset: number }
  | { status: "ready"; data: BacktestSignalSummary[]; error?: never; offset: number }
  | { status: "error"; data?: never; error: unknown; offset: number };

const PAGE_SIZE = 20;

export function BacktestDetailPage({ backtestId }: BacktestDetailPageProps) {
  return <BacktestDetailPageForId backtestId={backtestId} key={backtestId} />;
}

function BacktestDetailPageForId({ backtestId }: BacktestDetailPageProps) {
  const location = useLocation();
  const backHref = listReturnHref(location.state, "/backtests");
  const { state: backtestState, reload: reloadBacktest } = useResource({
    hasNotFoundState: true,
    key: backtestId,
    load: () => getBacktestDetail(backtestId)
  });
  const [activeTab, setActiveTab] = useState<"overview" | "signals">("overview");
  const [signalOffset, setSignalOffset] = useState(0);
  const [signalsState, setSignalsState] = useState<SignalsState>({ status: "idle" });
  const [signalReloadToken, setSignalReloadToken] = useState(0);
  const signalRequestKey = useRef(0);
  const loadedSignalOffset = useRef<number | null>(null);

  useDocumentTitle(`Backtest Detail #${backtestId}`);

  useEffect(() => {
    if (activeTab !== "signals" || backtestState.status !== "ready" || backtestState.data.signal_count === 0) {
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
          setSignalsState({ status: "error", error, offset: signalOffset });
        }
      });
  }, [activeTab, backtestId, backtestState, signalOffset, signalReloadToken]);

  function retrySignals() {
    setSignalsState({ status: "loading", offset: signalOffset });
    setSignalReloadToken((value) => value + 1);
  }

  return (
    <section className="page detail-page">
      <div className="page-heading">
        <Link className="operation-link detail-back-link" to={backHref}>
          ← Back to Backtests
        </Link>
        <p>Backtest research workspace</p>
        <h1>Backtest Detail</h1>
      </div>
      {renderBacktestDetail(
        backtestState,
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
        signalsState,
        reloadBacktest,
        retrySignals
      )}
    </section>
  );
}

function renderBacktestDetail(
  backtestState: ResourceState<BacktestDetailResponse>,
  backtestId: string,
  activeTab: "overview" | "signals",
  setActiveTab: (tab: "overview" | "signals") => void,
  signalOffset: number,
  setSignalOffset: (offset: number) => void,
  signalsState: SignalsState,
  retry: () => void,
  retrySignals: () => void
) {
  if (backtestState.status === "loading") {
    return <FeedbackMessage variant="loading">Loading backtest detail.</FeedbackMessage>;
  }

  if (backtestState.status === "not-found") {
    return <EmptyState>Backtest run {backtestId} was not found.</EmptyState>;
  }

  if (backtestState.status === "error") {
    return <ReadFailure error={backtestState.error} label="Backtest detail" onRetry={retry} />;
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
  const tabs = [
    ["overview", "Overview"],
    ["signals", `Signals (${signalCount})`]
  ] as const;

  return (
    <article className="dashboard-panel">
      <strong className="panel-primary">Backtest #{run.run_id}</strong>
      <div aria-label="Backtest detail sections" className="backtest-tabs" role="tablist">
        {tabs.map(([tab, label]) => (
          <button
            aria-controls={`backtest-${tab}-panel`}
            aria-selected={activeTab === tab}
            className="backtest-tab"
            id={`backtest-${tab}-tab`}
            key={tab}
            onClick={() => selectTab(tab)}
            onKeyDown={onTabKeyDown}
            role="tab"
            tabIndex={activeTab === tab ? 0 : -1}
            type="button"
          >
            {label}
          </button>
        ))}
      </div>
      {activeTab === "overview" ? (
      <div aria-labelledby="backtest-overview-tab" id="backtest-overview-panel" role="tabpanel">
      <p className="run-summary">
        <strong>{run.strategy_id}</strong>
        <span aria-hidden="true"> · </span>
        <span className="mono-compact">{formatDate(run.start_date)}</span>
        {" to "}
        <span className="mono-compact">{formatDate(run.end_date)}</span>
        <span aria-hidden="true"> · </span>
        <span className="run-summary-status">{run.status}</span>
      </p>
      <DecisionSummarySection
        benchmarks={backtestState.data.benchmarks ?? []}
        metrics={metrics}
      />
      <section className="holdings-section" aria-labelledby="backtest-equity-curve-heading">
        <h3 id="backtest-equity-curve-heading">Equity curve</h3>
        <EquityCurveChart
          points={backtestState.data.equity_curve}
          benchmarks={backtestState.data.benchmarks ?? []}
        />
      </section>
      <BenchmarkComparisonSection
        benchmarks={backtestState.data.benchmarks ?? []}
        metrics={metrics}
      />
      <DeepAnalysisSection
        benchmarks={backtestState.data.benchmarks ?? []}
        metrics={metrics}
        returnStability={backtestState.data.return_stability}
      />
      <ExperimentConfigSection run={run} />
      </div>
      ) : (
        <SignalsPanel count={signalCount} offset={signalOffset} retry={retrySignals} setOffset={setSignalOffset} state={signalsState} />
      )}
    </article>
  );
}

function SignalsPanel({ count, offset, retry, setOffset, state }: { count: number; offset: number; retry: () => void; setOffset: (offset: number) => void; state: SignalsState }) {
  return <section aria-labelledby="backtest-signals-tab" className="holdings-section" id="backtest-signals-panel" role="tabpanel">
    {count === 0 ? <EmptyState>No signals are linked to this backtest.</EmptyState> : state.status === "loading" || state.status === "idle" ? <FeedbackMessage variant="loading">Loading backtest signals.</FeedbackMessage> : state.status === "error" ? <ReadFailure error={state.error} label="Backtest signals" onRetry={retry} /> : <><ScrollableTableWrap label="Backtest signals"><table className="holdings-table"><TableHeader columns={["Signal #", "Signal date", "Result", "Action"]} /><tbody>{state.data.map((signal) => <tr key={signal.signal_id}><TableCells classNames={["mono-compact", "mono-compact", undefined, "mono-compact"]} cells={[signal.signal_id, formatDate(signal.signal_date), formatNullableText(signal.result), <Link className="operation-link" to={`/signals/${signal.signal_id}`}>Signal #{signal.signal_id}</Link>]} /></tr>)}</tbody></table></ScrollableTableWrap><Pagination itemCount={state.data.length} offset={offset} onOffsetChange={setOffset} pageSize={PAGE_SIZE} totalCount={count} /></>}
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
          {[
            ["Point count", formatInteger(1)],
            ["Trade date", formatDate(point.tradeDate)],
            ["Net value", formatNetValue(point.netValue)]
          ].map(([label, value]) => (
            <DescriptionItem key={label} label={label} value={value} mono />
          ))}
        </dl>
      </div>
    );
  }

  const geometry = computeMultiEquityCurveGeometry(chartSeries);
  const legacyGeometry = geometry.series.length === 1 ? computeEquityCurveGeometry(chartPoints) : null;
  const firstPoint = chartPoints[0];
  const lastPoint = chartPoints[chartPoints.length - 1];
  return (
    <div className="equity-curve-card">
      <EquityCurvePlot
        endLabelTestIdPrefix="equity-curve-end-label-"
        geometry={geometry}
        highlightCoordinates={legacyGeometry?.highlightCoordinates}
        labelledBy="equity-curve-chart-title"
        legendLabel="Equity curve legend"
        lineTestIdPrefix="equity-curve-line-"
        singleLineTestId="equity-curve-line"
        title="Equity curve net value chart"
        xTickTestId="equity-curve-x-tick"
        yTickTestId="equity-curve-y-tick"
      />
      <dl className="equity-curve-summary">
        {[
          ["Point count", formatInteger(chartPoints.length)],
          ["Start point", formatEquityCurvePoint(firstPoint)],
          ["End point", formatEquityCurvePoint(lastPoint)],
          ["Min net value", formatNetValue(geometry.minNetValue)],
          ["Max net value", formatNetValue(geometry.maxNetValue)]
        ].map(([label, value]) => (
          <DescriptionItem key={label} label={label} value={value} mono />
        ))}
      </dl>
    </div>
  );
}
