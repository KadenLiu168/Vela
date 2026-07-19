import { useEffect, useState } from "react";
import {
  ApiClientError,
  type BacktestDetailResponse,
  getBacktestDetail
} from "../api/client";
import { DescriptionItem, EmptyState, FeedbackMessage } from "../components";
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

export function BacktestDetailPage({ backtestId }: BacktestDetailPageProps) {
  const [backtestState, setBacktestState] = useState<BacktestDetailState>({
    status: "loading"
  });

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

  return (
    <section className="page detail-page">
      <div className="page-heading">
        <p>Backtest research workspace</p>
        <h1>Backtest Detail</h1>
      </div>
      {renderBacktestDetail(getBacktestDetailState(backtestState, backtestId), backtestId)}
    </section>
  );
}

function getBacktestDetailState(state: BacktestDetailState, backtestId: string): BacktestDetailState {
  return state.status === "loading" || state.backtestId === backtestId ? state : { status: "loading" };
}

function renderBacktestDetail(backtestState: BacktestDetailState, backtestId: string) {
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
  const signalIds = backtestState.data.signal_ids;
  const signalCount = backtestState.data.signal_count;

  return (
    <article className="dashboard-panel">
      <strong className="panel-primary">Backtest #{run.run_id}</strong>
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
      <section className="holdings-section" aria-labelledby="backtest-signals-heading">
        <h3 id="backtest-signals-heading">Signals ({signalCount})</h3>
        {signalIds.length === 0 ? (
          <EmptyState>No signals are linked to this backtest.</EmptyState>
        ) : (
          <ul>
            {signalIds.map((signalId) => (
              <li key={signalId}>
                <a className="operation-link" href={`/signals/${signalId}`}>
                  Signal #{signalId}
                </a>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className="holdings-section" aria-labelledby="backtest-equity-curve-heading">
        <h3 id="backtest-equity-curve-heading">Equity curve</h3>
        <EquityCurveChart points={backtestState.data.equity_curve} />
      </section>
      <section className="holdings-section" aria-labelledby="backtest-parameters-heading">
        <h3 id="backtest-parameters-heading">Parameters</h3>
        <pre className="parameter-summary">{formatParameterSummary(run.parameters_json)}</pre>
      </section>
    </article>
  );
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
