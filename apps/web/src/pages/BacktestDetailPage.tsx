import { useEffect, useState } from "react";
import {
  ApiClientError,
  type BacktestDetailResponse,
  type BacktestEquityCurvePoint,
  getBacktestDetail
} from "../api/client";
import { FeedbackMessage } from "../components/FeedbackMessage";
import {
  formatDate,
  formatDecimal,
  formatInteger,
  formatNullableText,
  formatNetValue,
  formatRatioAsPercent,
  formatTimestamp
} from "../utils/formatters";

type BacktestDetailPageProps = {
  backtestId: string;
};

type BacktestDetailState =
  | { status: "loading"; backtestId: string; data?: never; error?: never }
  | { status: "ready"; backtestId: string; data: BacktestDetailResponse; error?: never }
  | { status: "not-found"; backtestId: string; data?: never; error?: never }
  | { status: "error"; backtestId: string; data?: never; error: string };

export function BacktestDetailPage({ backtestId }: BacktestDetailPageProps) {
  const [backtestState, setBacktestState] = useState<BacktestDetailState>({
    status: "loading",
    backtestId
  });

  useEffect(() => {
    let isCurrent = true;

    getBacktestDetail(backtestId)
      .then((data) => {
        if (isCurrent) {
          setBacktestState({ status: "ready", backtestId, data });
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
          backtestId,
          error: error instanceof ApiClientError ? error.kind : "unavailable"
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
        <h2>Backtest Detail</h2>
      </div>
      {renderBacktestDetail(getCurrentBacktestState(backtestState, backtestId), backtestId)}
    </section>
  );
}

function getCurrentBacktestState(
  backtestState: BacktestDetailState,
  backtestId: string
): BacktestDetailState {
  if (backtestState.backtestId === backtestId) {
    return backtestState;
  }

  return { status: "loading", backtestId };
}

function renderBacktestDetail(backtestState: BacktestDetailState, backtestId: string) {
  if (backtestState.status === "loading") {
    return <FeedbackMessage variant="loading">Loading backtest detail.</FeedbackMessage>;
  }

  if (backtestState.status === "not-found") {
    return <p className="empty-state">Backtest run {backtestId} was not found.</p>;
  }

  if (backtestState.status === "error") {
    return (
      <FeedbackMessage className="dashboard-alert" variant="error">
        Backtest detail API unavailable: {backtestState.error}
      </FeedbackMessage>
    );
  }

  const { metrics, run } = backtestState.data;

  return (
    <article className="dashboard-panel">
      <strong className="panel-primary">Backtest #{run.run_id}</strong>
      <dl className="compact-list">
        <Detail label="Strategy" value={run.strategy_name} />
        <Detail label="Config version" value={run.config_version} />
        <Detail label="Date range" value={`${formatDate(run.start_date)} to ${formatDate(run.end_date)}`} />
        <Detail label="Status" value={run.status} />
        <Detail label="Started at" value={formatTimestamp(run.started_at)} />
        <Detail label="Finished at" value={formatTimestamp(run.finished_at)} />
        <Detail label="Error message" value={formatNullableText(run.error_message)} />
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
    </article>
  );
}

type EquityCurveChartPoint = {
  tradeDate: string;
  netValue: number;
};

function EquityCurveChart({ points }: { points: BacktestEquityCurvePoint[] }) {
  const chartPoints = getValidEquityCurvePoints(points);

  if (chartPoints.length === 0) {
    return <p className="empty-state">No valid equity curve points are available for this run.</p>;
  }

  if (chartPoints.length === 1) {
    const point = chartPoints[0];

    return (
      <div className="equity-curve-single-point">
        <p className="empty-state">Only one equity curve point is available.</p>
        <dl className="equity-curve-summary">
          <Detail label="Point count" value={formatInteger(1)} />
          <Detail label="Trade date" value={formatDate(point.tradeDate)} />
          <Detail label="Net value" value={formatNetValue(point.netValue)} />
        </dl>
      </div>
    );
  }

  const path = buildEquityCurvePath(chartPoints);
  const firstPoint = chartPoints[0];
  const lastPoint = chartPoints[chartPoints.length - 1];
  const netValues = chartPoints.map((point) => point.netValue);
  const minNetValue = Math.min(...netValues);
  const maxNetValue = Math.max(...netValues);

  return (
    <div className="equity-curve-card">
      <svg
        aria-labelledby="equity-curve-chart-title"
        className="equity-curve-chart"
        role="img"
        viewBox="0 0 640 220"
      >
        <title id="equity-curve-chart-title">Equity curve net value chart</title>
        <line className="equity-curve-grid-line" x1="48" x2="608" y1="24" y2="24" />
        <line className="equity-curve-grid-line" x1="48" x2="608" y1="176" y2="176" />
        <path className="equity-curve-line" d={path} data-testid="equity-curve-line" />
      </svg>
      <dl className="equity-curve-summary">
        <Detail label="Point count" value={formatInteger(chartPoints.length)} />
        <Detail label="Start point" value={formatEquityCurvePoint(firstPoint)} />
        <Detail label="End point" value={formatEquityCurvePoint(lastPoint)} />
        <Detail label="Min net value" value={formatNetValue(minNetValue)} />
        <Detail label="Max net value" value={formatNetValue(maxNetValue)} />
      </dl>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
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

function getValidEquityCurvePoints(points: BacktestEquityCurvePoint[]): EquityCurveChartPoint[] {
  return points.flatMap((point) => {
    if (point.net_value === null) {
      return [];
    }

    const netValue = Number(point.net_value);
    return Number.isFinite(netValue) ? [{ tradeDate: point.trade_date, netValue }] : [];
  });
}

function buildEquityCurvePath(points: EquityCurveChartPoint[]): string {
  const chart = {
    height: 220,
    paddingBottom: 44,
    paddingLeft: 48,
    paddingRight: 32,
    paddingTop: 24,
    width: 640
  };
  const drawableWidth = chart.width - chart.paddingLeft - chart.paddingRight;
  const drawableHeight = chart.height - chart.paddingTop - chart.paddingBottom;
  const netValues = points.map((point) => point.netValue);
  const minNetValue = Math.min(...netValues);
  const maxNetValue = Math.max(...netValues);
  const netValueRange = maxNetValue - minNetValue;

  return points
    .map((point, index) => {
      const x = chart.paddingLeft + (drawableWidth * index) / (points.length - 1);
      const normalizedY =
        netValueRange === 0 ? 0.5 : (maxNetValue - point.netValue) / netValueRange;
      const y = chart.paddingTop + normalizedY * drawableHeight;
      const command = index === 0 ? "M" : "L";

      return `${command} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

function formatEquityCurvePoint(point: EquityCurveChartPoint): string {
  return `${formatDate(point.tradeDate)} / ${formatNetValue(point.netValue)}`;
}

function formatParameterSummary(value: string | null): string {
  if (!value) {
    return formatNullableText(value);
  }

  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return value;
  }
}
