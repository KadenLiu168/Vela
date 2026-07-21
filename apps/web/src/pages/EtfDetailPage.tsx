import {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type MouseEvent as ReactMouseEvent
} from "react";
import {
  ApiClientError,
  type EtfPriceTrendPoint,
  type EtfPriceTrendResponse,
  type PriceTrendRange,
  getEtfPriceTrend
} from "../api/client";
import { DescriptionItem, EmptyState, FeedbackMessage } from "../components";
import { formatDate, formatDecimal } from "../utils/formatters";
import {
  computeTrendGeometry,
  indexFromX,
  TREND_CHART,
  trendDateAxisIndexes,
  type TrendGeometry
} from "./etfTrendChart";

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

type EtfDetailRequestKey = `${string}:${PriceTrendRange}`;

type EtfDetailState =
  | { status: "loading"; data?: never; error?: never; requestKey?: never }
  | { status: "ready"; data: EtfPriceTrendResponse; error?: never; requestKey: EtfDetailRequestKey }
  | { status: "not-found"; data?: never; error?: never; requestKey: EtfDetailRequestKey }
  | { status: "error"; data?: never; error: string; requestKey: EtfDetailRequestKey };

export function EtfDetailPage({ etfId }: EtfDetailPageProps) {
  const [range, setRange] = useState<PriceTrendRange>("1y");
  const [state, setState] = useState<EtfDetailState>({ status: "loading" });

  useEffect(() => {
    let isCurrent = true;
    const requestKey = getEtfDetailRequestKey(etfId, range);

    getEtfPriceTrend(etfId, range)
      .then((data) => {
        if (isCurrent) {
          setState({ status: "ready", data, requestKey });
        }
      })
      .catch((error: unknown) => {
        if (!isCurrent) {
          return;
        }

        if (error instanceof ApiClientError && error.status === 404) {
          setState({ status: "not-found", requestKey });
          return;
        }

        setState({
          status: "error",
          error: error instanceof ApiClientError ? error.kind : "unavailable",
          requestKey
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
      {renderEtfDetail(getEtfDetailState(state, etfId, range), etfId, range, setRange)}
    </section>
  );
}

function getEtfDetailRequestKey(etfId: string, range: PriceTrendRange): EtfDetailRequestKey {
  return `${etfId}:${range}`;
}

function getEtfDetailState(
  state: EtfDetailState,
  etfId: string,
  range: PriceTrendRange
): EtfDetailState {
  const requestKey = getEtfDetailRequestKey(etfId, range);
  return state.status === "loading" || state.requestKey === requestKey ? state : { status: "loading" };
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

function TrendChart({ points }: { points: EtfPriceTrendPoint[] }) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const chartPoints = useMemo(() => getValidTrendPoints(points), [points]);
  const isMultiPoint = chartPoints.length >= 2;
  const geometry = useMemo(
    () => (isMultiPoint ? computeTrendGeometry(chartPoints) : null),
    [chartPoints, isMultiPoint]
  );
  const dateAxisIndexes = useMemo(
    () => (geometry ? trendDateAxisIndexes(geometry.pointCount) : []),
    [geometry]
  );
  const dateLabels = useMemo(
    () => dateAxisIndexes.map((index) => formatDate(chartPoints[index].tradeDate)),
    [chartPoints, dateAxisIndexes]
  );
  const handleHoverMove = useCallback(
    (event: ReactMouseEvent<SVGRectElement>) => {
      if (!geometry) {
        return;
      }
      const rect = event.currentTarget.getBoundingClientRect();
      const viewBoxX = (event.clientX - rect.left) * (TREND_CHART.width / rect.width);
      const next = indexFromX(viewBoxX, geometry.pointCount);
      setHoverIndex((prev) => (prev === next ? prev : next));
    },
    [geometry]
  );

  if (chartPoints.length === 0) {
    return <EmptyState>No price data is available for this ETF and horizon.</EmptyState>;
  }

  if (chartPoints.length === 1) {
    const point = chartPoints[0];

    return (
      <div className="trend-single-point">
        <EmptyState>Only one price point is available.</EmptyState>
        <dl className="trend-readout">
          <DescriptionItem label="Trade date" value={formatDate(point.tradeDate)} />
          <DescriptionItem label="Price" value={formatDecimal(point.price, 4)} />
        </dl>
      </div>
    );
  }

  // chartPoints.length >= 2 here, so geometry is non-null; the guard narrows the type.
  if (!geometry) {
    return null;
  }

  const activeIndex = hoverIndex ?? geometry.pointCount - 1;
  const activePoint = chartPoints[activeIndex];

  return (
    <div className="trend-chart-card">
      <svg
        aria-labelledby="trend-chart-title"
        className="trend-chart"
        onMouseLeave={() => setHoverIndex(null)}
        role="img"
        viewBox={`0 0 ${TREND_CHART.width} ${TREND_CHART.height}`}
      >
        <title id="trend-chart-title">ETF forward-adjusted price trend</title>
        <TrendChartFrame
          dateAxisIndexes={dateAxisIndexes}
          dateLabels={dateLabels}
          geometry={geometry}
          onHoverMove={handleHoverMove}
        />
        <TrendHighlight cx={geometry.x(activeIndex)} cy={geometry.y(Number(activePoint.price))} />
      </svg>
      <TrendReadout tradeDate={activePoint.tradeDate} price={activePoint.price} />
    </div>
  );
}

const TrendChartFrame = memo(
  function TrendChartFrame({
    dateAxisIndexes,
    dateLabels,
    geometry,
    onHoverMove
  }: {
    dateAxisIndexes: number[];
    dateLabels: string[];
    geometry: TrendGeometry;
    onHoverMove: (event: ReactMouseEvent<SVGRectElement>) => void;
  }) {
    return (
      <>
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
          y1={TREND_CHART.paddingTop + geometry.drawableHeight}
          y2={TREND_CHART.paddingTop + geometry.drawableHeight}
        />
        <text
          className="trend-axis-label trend-axis-price"
          data-testid="trend-axis-price"
          textAnchor="end"
          x={TREND_CHART.paddingLeft - 8}
          y={TREND_CHART.paddingTop + 4}
        >
          {formatDecimal(String(geometry.maxPrice), 4)}
        </text>
        <text
          className="trend-axis-label trend-axis-price"
          data-testid="trend-axis-price"
          textAnchor="end"
          x={TREND_CHART.paddingLeft - 8}
          y={TREND_CHART.paddingTop + geometry.drawableHeight}
        >
          {formatDecimal(String(geometry.minPrice), 4)}
        </text>
        <path className="trend-line" d={geometry.linePath} data-testid="trend-line" />
        {dateAxisIndexes.map((index, labelIndex) => (
          <text
            className="trend-axis-label trend-axis-date"
            data-testid="trend-axis-date"
            key={index}
            textAnchor="middle"
            x={geometry.x(index)}
            y={TREND_CHART.height - TREND_CHART.paddingBottom + 18}
          >
            {dateLabels[labelIndex]}
          </text>
        ))}
        <rect
          className="trend-hover-overlay"
          data-testid="trend-hover-overlay"
          height={geometry.drawableHeight}
          onMouseMove={onHoverMove}
          width={geometry.drawableWidth}
          x={TREND_CHART.paddingLeft}
          y={TREND_CHART.paddingTop}
        />
      </>
    );
  }
);

const TrendHighlight = memo(function TrendHighlight({ cx, cy }: { cx: number; cy: number }) {
  return <circle className="trend-highlight" cx={cx} cy={cy} data-testid="trend-highlight" r="4" />;
});

const TrendReadout = memo(
  function TrendReadout({ tradeDate, price }: { tradeDate: string; price: string }) {
    return (
      <dl className="trend-readout" data-testid="trend-readout">
        <DescriptionItem label="Trade date" value={formatDate(tradeDate)} />
        <DescriptionItem label="Price" value={formatDecimal(price, 4)} />
      </dl>
    );
  }
);

function getValidTrendPoints(points: EtfPriceTrendPoint[]): TrendChartPoint[] {
  return points.flatMap((point) => {
    const price = Number(point.price);
    return Number.isFinite(price)
      ? [{ tradeDate: point.trade_date, price: point.price }]
      : [];
  });
}
