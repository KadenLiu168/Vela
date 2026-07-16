// Pure geometry helpers for the ETF price-trend chart. Extracted from EtfDetailPage so the
// hover-index math is unit-testable without jsdom layout and the page module only exports
// components (keeps React Fast Refresh happy).

export const TREND_CHART = {
  height: 260,
  paddingBottom: 44,
  paddingLeft: 56,
  paddingRight: 16,
  paddingTop: 16,
  width: 640
};

export type TrendGeometry = {
  drawableWidth: number;
  drawableHeight: number;
  minPrice: number;
  maxPrice: number;
  pointCount: number;
  x: (index: number) => number;
  y: (price: number) => number;
  linePath: string;
};

// Map a pointer x-coordinate (in viewBox units) to the nearest data-point index on the
// point grid (drawableWidth / (pointCount - 1)), clamped to the series bounds. Pure -- no
// DOM -- so it is unit-testable without jsdom layout. The screen-to-viewBox conversion
// lives in the mousemove handler, not here. Requires pointCount >= 2 (the caller renders
// single-point and empty states without invoking this).
export function indexFromX(viewBoxX: number, pointCount: number): number {
  const drawableWidth = TREND_CHART.width - TREND_CHART.paddingLeft - TREND_CHART.paddingRight;
  const pointSpacing = drawableWidth / (pointCount - 1);
  const index = Math.round((viewBoxX - TREND_CHART.paddingLeft) / pointSpacing);
  return Math.min(Math.max(index, 0), pointCount - 1);
}

export function computeTrendGeometry(points: { price: string }[]): TrendGeometry {
  const drawableWidth = TREND_CHART.width - TREND_CHART.paddingLeft - TREND_CHART.paddingRight;
  const drawableHeight = TREND_CHART.height - TREND_CHART.paddingTop - TREND_CHART.paddingBottom;
  const numericPrices = points.map((point) => Number(point.price));
  const minPrice = Math.min(...numericPrices);
  const maxPrice = Math.max(...numericPrices);
  const priceRange = maxPrice - minPrice;
  const pointCount = points.length;

  const x = (index: number) => TREND_CHART.paddingLeft + (drawableWidth * index) / (pointCount - 1);
  const y = (price: number) =>
    TREND_CHART.paddingTop +
    (priceRange === 0
      ? drawableHeight / 2
      : ((maxPrice - price) / priceRange) * drawableHeight);

  const linePath = points
    .map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${x(index).toFixed(2)} ${y(Number(point.price)).toFixed(2)}`;
    })
    .join(" ");

  return { drawableWidth, drawableHeight, minPrice, maxPrice, pointCount, x, y, linePath };
}

export function trendDateAxisIndexes(pointCount: number): number[] {
  return Array.from(new Set([0, Math.floor((pointCount - 1) / 2), pointCount - 1]));
}
