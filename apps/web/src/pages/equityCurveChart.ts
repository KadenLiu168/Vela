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
  endpoints: {
    first: EquityCurveChartCoordinate;
    last: EquityCurveChartCoordinate;
  };
};

export type EquityCurveChartDateTick = {
  value: string;
  x: number;
};

export type EquityCurveChartValueTick = {
  value: number;
  y: number;
};

export type EquityCurveChartMultiGeometry = {
  minNetValue: number;
  maxNetValue: number;
  dateTicks: EquityCurveChartDateTick[];
  valueTicks: EquityCurveChartValueTick[];
  series: EquityCurveChartSeriesGeometry[];
};

export type EquityCurveChartEndLabel = {
  key: string;
  name: string;
  x: number;
  y: number;
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

export function computeMultiEquityCurveGeometry(series: EquityCurveChartSeries[]): EquityCurveChartMultiGeometry {
  const validSeries = series.filter((item) => item.points.length > 0);
  const allPoints = validSeries.flatMap((item) => item.points);
  const netValues = allPoints.map((point) => point.netValue);
  const minNetValue = netValues.length === 0 ? 0 : Math.min(...netValues);
  const maxNetValue = netValues.length === 0 ? 0 : Math.max(...netValues);
  const netValueRange = maxNetValue - minNetValue;
  const dates = [...new Set(allPoints.map((point) => point.tradeDate))].sort();
  const dateIndexes = new Map(dates.map((tradeDate, index) => [tradeDate, index]));
  const drawableWidth = EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingLeft - EQUITY_CURVE_CHART.paddingRight;
  const drawableHeight = EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingTop - EQUITY_CURVE_CHART.paddingBottom;

  if (validSeries.length === 0) {
    return { minNetValue: 0, maxNetValue: 0, dateTicks: [], valueTicks: [], series: [] };
  }

  return {
    minNetValue,
    maxNetValue,
    dateTicks: computeDateTicks(dates, drawableWidth),
    valueTicks: computeValueTicks(minNetValue, maxNetValue, netValueRange, drawableHeight),
    series: validSeries.map((item) => {
      const coordinates = item.points.map((point) => {
        const dateIndex = dateIndexes.get(point.tradeDate) ?? 0;
        const x = EQUITY_CURVE_CHART.paddingLeft + (drawableWidth * dateIndex) / Math.max(dates.length - 1, 1);
        const normalizedY = netValueRange === 0 ? 0.5 : (maxNetValue - point.netValue) / netValueRange;
        const y = EQUITY_CURVE_CHART.paddingTop + normalizedY * drawableHeight;
        return { index: 0, x, y };
      });
      return {
        ...item,
        linePath: coordinates
          .map((coordinate, index) => `${index === 0 ? "M" : "L"} ${coordinate.x.toFixed(2)} ${coordinate.y.toFixed(2)}`)
          .join(" "),
        endpoints: {
          first: { index: 0, x: coordinates[0].x, y: coordinates[0].y },
          last: { index: coordinates.length - 1, x: coordinates[coordinates.length - 1].x, y: coordinates[coordinates.length - 1].y }
        }
      };
    })
  };
}

const MAX_DATE_TICKS = 5;

function computeDateTicks(dates: string[], drawableWidth: number): EquityCurveChartDateTick[] {
  if (dates.length === 0) {
    return [];
  }

  if (dates.length <= MAX_DATE_TICKS) {
    return dates.map((value, index) => ({
      value,
      x: EQUITY_CURVE_CHART.paddingLeft + (drawableWidth * index) / Math.max(dates.length - 1, 1)
    }));
  }

  const indexes = Array.from(
    new Set(
      Array.from({ length: MAX_DATE_TICKS }, (_, index) =>
        Math.round((index * (dates.length - 1)) / (MAX_DATE_TICKS - 1))
      )
    )
  );
  return indexes.map((index) => ({
    value: dates[index],
    x: EQUITY_CURVE_CHART.paddingLeft + (drawableWidth * index) / (dates.length - 1)
  }));
}

function computeValueTicks(
  minNetValue: number,
  maxNetValue: number,
  netValueRange: number,
  drawableHeight: number
): EquityCurveChartValueTick[] {
  if (netValueRange === 0) {
    return [
      {
        value: minNetValue,
        y: EQUITY_CURVE_CHART.paddingTop + drawableHeight / 2
      }
    ];
  }

  const rawStep = netValueRange / 4;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalized = rawStep / magnitude;
  const niceFactor = normalized >= 5 ? 5 : normalized >= 2.5 ? 2.5 : normalized >= 2 ? 2 : 1;
  const step = niceFactor * magnitude;
  const start = Math.ceil(minNetValue / step) * step;
  const values: number[] = [];
  for (let value = start; value <= maxNetValue + step * 1e-9; value += step) {
    const rounded = Math.abs(value) < step * 1e-9 ? 0 : Number(value.toFixed(10));
    values.push(rounded);
  }
  if (values.length < 2) {
    values.push(Number((start + step).toFixed(10)));
  }

  return values.map((value) => ({
    value,
    y: EQUITY_CURVE_CHART.paddingTop + ((maxNetValue - value) / netValueRange) * drawableHeight
  }));
}

const MIN_END_LABEL_GAP = 16;

/** Deterministic vertical separation for direct end-labels so converged
 *  endpoints stay readable, clamped inside the SVG viewBox. When the
 *  separated group overflows the bottom edge, the whole group shifts up so
 *  the last label lands on the boundary; the current three-series contract
 *  keeps the shifted group inside the top boundary as well. */
export function computeSeriesEndLabels(series: EquityCurveChartSeriesGeometry[]): EquityCurveChartEndLabel[] {
  const rightX = EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingRight;
  const minY = EQUITY_CURVE_CHART.paddingTop + 4;
  const maxY = EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom - 4;

  const ordered = series
    .map((item) => ({ key: item.key, name: item.name, y: item.endpoints.last.y }))
    .sort((a, b) => a.y - b.y);

  const raw: { key: string; name: string; y: number }[] = [];
  for (const entry of ordered) {
    let y = entry.y;
    const previous = raw[raw.length - 1];
    if (previous && y - previous.y < MIN_END_LABEL_GAP) {
      y = previous.y + MIN_END_LABEL_GAP;
    }
    raw.push({ key: entry.key, name: entry.name, y });
  }

  const lastRawY = raw[raw.length - 1]?.y ?? 0;
  const shift = Math.max(0, lastRawY - maxY);

  return raw.map((entry) => ({
    key: entry.key,
    name: entry.name,
    x: rightX,
    y: Math.round(Math.min(Math.max(entry.y - shift, minY), maxY) * 100) / 100
  }));
}
