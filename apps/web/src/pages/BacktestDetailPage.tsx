import { useEffect, useRef, useState } from "react";
import {
  ApiClientError,
  type BacktestDetailResponse,
  type BacktestSignalSummary,
  getBacktestDetail,
  listBacktestSignals
} from "../api/client";
import { DescriptionItem, EmptyState, FeedbackMessage, Pagination } from "../components";
import {
  formatDate,
  formatDecimal,
  formatInteger,
  formatNullableText,
  formatNetValue,
  formatRatioAsPercent,
  formatTimestamp
} from "../utils/formatters";
import { formatEquityCurvePoint, formatParameterSummary } from "./backtestFormatters";
import {
  computeEquityCurveGeometry,
  EQUITY_CURVE_CHART,
  normalizeEquityCurvePoints
} from "./equityCurveChart";

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
        <dl className="metric-card-grid">
          <MetricCard label="Total return" value={formatRatioAsPercent(metrics.total_return)} />
          <MetricCard
            label="Annualized return"
            value={formatRatioAsPercent(metrics.annualized_return)}
          />
          <MetricCard label="Max drawdown" value={formatRatioAsPercent(metrics.max_drawdown)} />
          <MetricCard label="Volatility" value={formatRatioAsPercent(metrics.volatility)} />
          <MetricCard label="Sharpe ratio" value={formatDecimal(metrics.sharpe_ratio, 2, false)} />
        </dl>
      </section>
      <section className="holdings-section" aria-labelledby="backtest-equity-curve-heading">
        <h3 id="backtest-equity-curve-heading">Equity curve</h3>
        <EquityCurveChart points={backtestState.data.equity_curve} />
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
    {count === 0 ? <EmptyState>No signals are linked to this backtest.</EmptyState> : state.status === "loading" || state.status === "idle" ? <FeedbackMessage variant="loading">Loading backtest signals.</FeedbackMessage> : state.status === "error" ? <FeedbackMessage variant="error">Backtest signals API unavailable: {state.error}</FeedbackMessage> : <><div className="holdings-table-wrap"><table className="holdings-table"><thead><tr><th scope="col">Signal #</th><th scope="col">Signal date</th><th scope="col">Result</th><th scope="col">Action</th></tr></thead><tbody>{state.data.map((signal) => <tr key={signal.signal_id}><td>{signal.signal_id}</td><td>{formatDate(signal.signal_date)}</td><td>{formatNullableText(signal.result)}</td><td><a className="operation-link" href={`/signals/${signal.signal_id}`}>Signal #{signal.signal_id}</a></td></tr>)}</tbody></table></div><Pagination itemCount={state.data.length} offset={offset} onOffsetChange={setOffset} pageSize={PAGE_SIZE} totalCount={count} /></>}
  </section>;
}

function EquityCurveChart({ points }: { points: BacktestDetailResponse["equity_curve"] }) {
  const chartPoints = normalizeEquityCurvePoints(points);

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

  const { highlightCoordinates, linePath, maxNetValue, minNetValue } = computeEquityCurveGeometry(chartPoints);
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
        <path className="equity-curve-line" d={linePath} data-testid="equity-curve-line" />
        {highlightCoordinates.map((coordinate) => (
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
