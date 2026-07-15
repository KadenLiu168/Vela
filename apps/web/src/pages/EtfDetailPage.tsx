import { useEffect, useState } from "react";
import {
  ApiClientError,
  type EtfPriceTrendPoint,
  type EtfPriceTrendResponse,
  type PriceTrendRange,
  getEtfPriceTrend
} from "../api/client";
import { EmptyState, FeedbackMessage } from "../components";
import { formatDate, formatDecimal } from "../utils/formatters";

type EtfDetailPageProps = {
  etfId: string;
};

type Horizon = {
  label: string;
  range: PriceTrendRange;
};

const HORIZONS: Horizon[] = [
  { label: "1M", range: "1m" },
  { label: "3M", range: "3m" },
  { label: "1Y", range: "1y" },
  { label: "3Y", range: "3y" },
  { label: "Max", range: "max" }
];

type EtfDetailState =
  | { status: "loading"; data?: never; error?: never }
  | { status: "ready"; data: EtfPriceTrendResponse; error?: never }
  | { status: "not-found"; data?: never; error?: never }
  | { status: "error"; data?: never; error: string };

export function EtfDetailPage({ etfId }: EtfDetailPageProps) {
  const [range, setRange] = useState<PriceTrendRange>("1y");
  const [state, setState] = useState<EtfDetailState>({ status: "loading" });

  useEffect(() => {
    let isCurrent = true;

    setState({ status: "loading" });

    getEtfPriceTrend(etfId, range)
      .then((data) => {
        if (isCurrent) {
          setState({ status: "ready", data });
        }
      })
      .catch((error: unknown) => {
        if (!isCurrent) {
          return;
        }

        if (error instanceof ApiClientError && error.status === 404) {
          setState({ status: "not-found" });
          return;
        }

        setState({
          status: "error",
          error: error instanceof ApiClientError ? error.kind : "unavailable"
        });
      });

    return () => {
      isCurrent = false;
    };
  }, [etfId, range]);

  return (
    <section className="page detail-page etf-detail-page">
      <div className="page-heading">
        <p>ETF price trend</p>
        <h1>ETF Detail</h1>
      </div>
      {renderEtfDetail(state, etfId, range, setRange)}
    </section>
  );
}

function renderEtfDetail(
  state: EtfDetailState,
  etfId: string,
  range: PriceTrendRange,
  setRange: (range: PriceTrendRange) => void
) {
  if (state.status === "loading") {
    return <FeedbackMessage variant="loading">Loading ETF price trend.</FeedbackMessage>;
  }

  if (state.status === "not-found") {
    return <EmptyState>ETF {etfId} was not found.</EmptyState>;
  }

  if (state.status === "error") {
    return (
      <FeedbackMessage className="dashboard-alert" variant="error">
        ETF trend API unavailable: {state.error}
      </FeedbackMessage>
    );
  }

  const { etf, points } = state.data;

  return (
    <article className="dashboard-panel">
      <strong className="panel-primary">{`${etf.exchange}:${etf.symbol}`}</strong>
      <p className="etf-detail-name">{etf.name}</p>
      <div className="trend-horizon" role="group" aria-label="Price trend horizon">
        {HORIZONS.map((horizon) => (
          <button
            aria-pressed={horizon.range === range}
            className={
              horizon.range === range
                ? "trend-horizon-button trend-horizon-button-active"
                : "trend-horizon-button"
            }
            key={horizon.range}
            type="button"
            onClick={() => setRange(horizon.range)}
          >
            {horizon.label}
          </button>
        ))}
      </div>
      <section className="holdings-section" aria-labelledby="etf-trend-chart-heading">
        <h3 id="etf-trend-chart-heading">Price trend</h3>
        <TrendChart points={points} />
      </section>
    </article>
  );
}

type TrendChartPoint = {
  tradeDate: string;
  price: string;
};

const TREND_CHART = {
  height: 260,
  paddingBottom: 44,
  paddingLeft: 56,
  paddingRight: 16,
  paddingTop: 16,
  width: 640
};

function TrendChart({ points }: { points: EtfPriceTrendPoint[] }) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const chartPoints = getValidTrendPoints(points);

  if (chartPoints.length === 0) {
    return <EmptyState>No price data is available for this ETF and horizon.</EmptyState>;
  }

  if (chartPoints.length === 1) {
    const point = chartPoints[0];

    return (
      <div className="trend-single-point">
        <EmptyState>Only one price point is available.</EmptyState>
        <dl className="trend-readout">
          <Detail label="Trade date" value={formatDate(point.tradeDate)} />
          <Detail label="Price" value={formatDecimal(point.price, 4)} />
        </dl>
      </div>
    );
  }

  const drawableWidth = TREND_CHART.width - TREND_CHART.paddingLeft - TREND_CHART.paddingRight;
  const drawableHeight = TREND_CHART.height - TREND_CHART.paddingTop - TREND_CHART.paddingBottom;
  const numericPrices = chartPoints.map((point) => Number(point.price));
  const minPrice = Math.min(...numericPrices);
  const maxPrice = Math.max(...numericPrices);
  const priceRange = maxPrice - minPrice;
  const pointCount = chartPoints.length;

  const x = (index: number) => TREND_CHART.paddingLeft + (drawableWidth * index) / (pointCount - 1);
  const y = (price: number) =>
    TREND_CHART.paddingTop +
    (priceRange === 0
      ? drawableHeight / 2
      : ((maxPrice - price) / priceRange) * drawableHeight);

  const linePath = chartPoints
    .map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${x(index).toFixed(2)} ${y(Number(point.price)).toFixed(2)}`;
    })
    .join(" ");

  const activeIndex = hoverIndex ?? pointCount - 1;
  const activePoint = chartPoints[activeIndex];
  const bandWidth = drawableWidth / pointCount;
  const dateAxisIndexes = Array.from(
    new Set([0, Math.floor((pointCount - 1) / 2), pointCount - 1])
  );

  return (
    <div className="trend-chart-card">
      <svg
        aria-labelledby="trend-chart-title"
        className="trend-chart"
        onMouseLeave={() => setHoverIndex(null)}
        role="img"
        viewBox={`0 0 ${TREND_CHART.width} ${TREND_CHART.height}`}
      >
        <title id="trend-chart-title">ETF backward-adjusted price trend</title>
        <line
          className="trend-grid-line"
          x1={TREND_CHART.paddingLeft}
          x2={TREND_CHART.width - TREND_CHART.paddingRight}
          y1={TREND_CHART.paddingTop}
          y2={TREND_CHART.paddingTop}
        />
        <line
          className="trend-grid-line"
          x1={TREND_CHART.paddingLeft}
          x2={TREND_CHART.width - TREND_CHART.paddingRight}
          y1={TREND_CHART.paddingTop + drawableHeight}
          y2={TREND_CHART.paddingTop + drawableHeight}
        />
        <text
          className="trend-axis-label trend-axis-price"
          data-testid="trend-axis-price"
          textAnchor="end"
          x={TREND_CHART.paddingLeft - 8}
          y={TREND_CHART.paddingTop + 4}
        >
          {formatDecimal(String(maxPrice), 4)}
        </text>
        <text
          className="trend-axis-label trend-axis-price"
          data-testid="trend-axis-price"
          textAnchor="end"
          x={TREND_CHART.paddingLeft - 8}
          y={TREND_CHART.paddingTop + drawableHeight}
        >
          {formatDecimal(String(minPrice), 4)}
        </text>
        <path className="trend-line" d={linePath} data-testid="trend-line" />
        <circle
          className="trend-highlight"
          cx={x(activeIndex)}
          cy={y(Number(activePoint.price))}
          data-testid="trend-highlight"
          r="4"
        />
        {dateAxisIndexes.map((index) => (
          <text
            className="trend-axis-label trend-axis-date"
            data-testid="trend-axis-date"
            key={index}
            textAnchor="middle"
            x={x(index)}
            y={TREND_CHART.height - TREND_CHART.paddingBottom + 18}
          >
            {formatDate(chartPoints[index].tradeDate)}
          </text>
        ))}
        {chartPoints.map((point, index) => (
          <rect
            className="trend-hover-band"
            data-testid="trend-hover-band"
            height={drawableHeight}
            key={point.tradeDate}
            onMouseEnter={() => setHoverIndex(index)}
            width={bandWidth}
            x={TREND_CHART.paddingLeft + index * bandWidth}
            y={TREND_CHART.paddingTop}
          />
        ))}
      </svg>
      <dl className="trend-readout" data-testid="trend-readout">
        <Detail label="Trade date" value={formatDate(activePoint.tradeDate)} />
        <Detail label="Price" value={formatDecimal(activePoint.price, 4)} />
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

function getValidTrendPoints(points: EtfPriceTrendPoint[]): TrendChartPoint[] {
  return points.flatMap((point) => {
    const price = Number(point.price);
    return Number.isFinite(price)
      ? [{ tradeDate: point.trade_date, price: point.price }]
      : [];
  });
}
