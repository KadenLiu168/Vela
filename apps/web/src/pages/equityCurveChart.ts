export const EQUITY_CURVE_CHART = {
  height: 220,
  paddingBottom: 44,
  paddingLeft: 48,
  paddingRight: 32,
  paddingTop: 24,
  width: 640
};

export type EquityCurveChartPoint = {
  tradeDate: string;
  netValue: number;
};

export type EquityCurveChartCoordinate = {
  index: number;
  x: number;
  y: number;
};

export type EquityCurveChartSeries = {
  key: string;
  name: string;
  points: EquityCurveChartPoint[];
};

export type EquityCurveChartSeriesGeometry = EquityCurveChartSeries & {
  linePath: string;
};

type EquityCurveApiPoint = {
  trade_date: string;
  net_value: string | null;
};

export function normalizeEquityCurvePoints(points: EquityCurveApiPoint[]): EquityCurveChartPoint[] {
  return points.flatMap((point) => {
    if (point.net_value === null) {
      return [];
    }

    const netValue = Number(point.net_value);
    return Number.isFinite(netValue) ? [{ tradeDate: point.trade_date, netValue }] : [];
  });
}

export function computeEquityCurveGeometry(points: EquityCurveChartPoint[]) {
  const drawableWidth = EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingLeft - EQUITY_CURVE_CHART.paddingRight;
  const drawableHeight = EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingTop - EQUITY_CURVE_CHART.paddingBottom;
  const netValues = points.map((point) => point.netValue);
  const minNetValue = Math.min(...netValues);
  const maxNetValue = Math.max(...netValues);
  const netValueRange = maxNetValue - minNetValue;
  const coordinates = points.map((point, index) => {
    const x = EQUITY_CURVE_CHART.paddingLeft + (drawableWidth * index) / (points.length - 1);
    const normalizedY = netValueRange === 0 ? 0.5 : (maxNetValue - point.netValue) / netValueRange;
    const y = EQUITY_CURVE_CHART.paddingTop + normalizedY * drawableHeight;
    return { index, x, y };
  });
  const linePath = coordinates
    .map((coordinate, index) => `${index === 0 ? "M" : "L"} ${coordinate.x.toFixed(2)} ${coordinate.y.toFixed(2)}`)
    .join(" ");
  const highlightIndexes = new Set([
    points.length - 1,
    points.findIndex((point) => point.netValue === minNetValue),
    points.findIndex((point) => point.netValue === maxNetValue)
  ]);

  return {
    coordinates,
    highlightCoordinates: [...highlightIndexes].map((index) => coordinates[index]),
    linePath,
    maxNetValue,
    minNetValue
  };
}

export function computeMultiEquityCurveGeometry(
  series: EquityCurveChartSeries[]
): { maxNetValue: number; minNetValue: number; series: EquityCurveChartSeriesGeometry[] } {
  const validSeries = series.filter((item) => item.points.length > 0);
  const allPoints = validSeries.flatMap((item) => item.points);
  const netValues = allPoints.map((point) => point.netValue);
  const minNetValue = Math.min(...netValues);
  const maxNetValue = Math.max(...netValues);
  const netValueRange = maxNetValue - minNetValue;
  const dates = [...new Set(allPoints.map((point) => point.tradeDate))].sort();
  const dateIndexes = new Map(dates.map((tradeDate, index) => [tradeDate, index]));
  const drawableWidth = EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingLeft - EQUITY_CURVE_CHART.paddingRight;
  const drawableHeight = EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingTop - EQUITY_CURVE_CHART.paddingBottom;

  return {
    minNetValue,
    maxNetValue,
    series: validSeries.map((item) => ({
      ...item,
      linePath: item.points
        .map((point, index) => {
          const dateIndex = dateIndexes.get(point.tradeDate) ?? 0;
          const x = EQUITY_CURVE_CHART.paddingLeft + (drawableWidth * dateIndex) / Math.max(dates.length - 1, 1);
          const normalizedY = netValueRange === 0 ? 0.5 : (maxNetValue - point.netValue) / netValueRange;
          const y = EQUITY_CURVE_CHART.paddingTop + normalizedY * drawableHeight;
          return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
        })
        .join(" ")
    }))
  };
}
