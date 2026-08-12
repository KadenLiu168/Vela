import { expect, it } from "vitest";
import {
  computeEquityCurveGeometry,
  computeMultiEquityCurveGeometry,
  computeSeriesEndLabels,
  EQUITY_CURVE_CHART,
  normalizeEquityCurvePoints
} from "./equityCurveChart";

it("filters invalid values and computes bounded two-point and multi-point paths", () => {
  expect(
    normalizeEquityCurvePoints([
      { net_value: null, trade_date: "2026-01-01" },
      { net_value: "NaN", trade_date: "2026-01-02" },
      { net_value: "1.01", trade_date: "2026-01-03" },
      { net_value: "Infinity", trade_date: "2026-01-04" }
    ])
  ).toEqual([{ netValue: 1.01, tradeDate: "2026-01-03" }]);

  expect(
    computeEquityCurveGeometry([
      { netValue: 1, tradeDate: "2026-01-01" },
      { netValue: 2, tradeDate: "2026-01-02" }
    ]).linePath
  ).toBe("M 48.00 176.00 L 608.00 24.00");

  const geometry = computeEquityCurveGeometry([
    { netValue: 1, tradeDate: "2026-01-01" },
    { netValue: 1.5, tradeDate: "2026-01-02" },
    { netValue: 1.25, tradeDate: "2026-01-03" }
  ]);

  expect(geometry.coordinates).toEqual([
    { index: 0, x: 48, y: 176 },
    { index: 1, x: 328, y: 24 },
    { index: 2, x: 608, y: 100 }
  ]);
  expect(geometry.linePath).toBe("M 48.00 176.00 L 328.00 24.00 L 608.00 100.00");
  for (const coordinate of geometry.coordinates) {
    expect(coordinate.x).toBeGreaterThanOrEqual(EQUITY_CURVE_CHART.paddingLeft);
    expect(coordinate.x).toBeLessThanOrEqual(EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingRight);
    expect(coordinate.y).toBeGreaterThanOrEqual(EQUITY_CURVE_CHART.paddingTop);
    expect(coordinate.y).toBeLessThanOrEqual(EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom);
  }
});

it("uses one shared scale and date axis for multiple ordered series", () => {
  const geometry = computeMultiEquityCurveGeometry([
    {
      key: "strategy",
      name: "Strategy",
      points: [
        { netValue: 1, tradeDate: "2026-01-01" },
        { netValue: 1.2, tradeDate: "2026-01-03" }
      ]
    },
    {
      key: "csi_300_buy_hold",
      name: "CSI 300 buy-and-hold",
      points: [
        { netValue: 1, tradeDate: "2026-01-01" },
        { netValue: 0.9, tradeDate: "2026-01-02" },
        { netValue: 1.1, tradeDate: "2026-01-03" }
      ]
    }
  ]);

  expect(geometry.minNetValue).toBe(0.9);
  expect(geometry.maxNetValue).toBe(1.2);
  expect(geometry.series.map((item) => item.key)).toEqual(["strategy", "csi_300_buy_hold"]);
  expect(geometry.series[0].linePath).toBe("M 48.00 125.33 L 608.00 24.00");
  expect(geometry.series[1].linePath).toBe("M 48.00 125.33 L 328.00 176.00 L 608.00 74.67");
});

it("centers equal values and selects deterministic, deduplicated extrema highlights", () => {
  const equalGeometry = computeEquityCurveGeometry([
    { netValue: 1, tradeDate: "2026-01-01" },
    { netValue: 1, tradeDate: "2026-01-02" }
  ]);
  expect(equalGeometry.coordinates.map(({ y }) => y)).toEqual([100, 100]);
  expect(equalGeometry.highlightCoordinates.map(({ index }) => index)).toEqual([1, 0]);

  const tiedGeometry = computeEquityCurveGeometry([
    { netValue: 1, tradeDate: "2026-01-01" },
    { netValue: 2, tradeDate: "2026-01-02" },
    { netValue: 1, tradeDate: "2026-01-03" },
    { netValue: 2, tradeDate: "2026-01-04" }
  ]);
  expect(tiedGeometry.minNetValue).toBe(1);
  expect(tiedGeometry.maxNetValue).toBe(2);
  expect(tiedGeometry.highlightCoordinates.map(({ index }) => index)).toEqual([3, 0, 1]);
});

const threeSeriesFixture = () => [
  {
    key: "strategy",
    name: "Strategy",
    points: [
      { netValue: 1, tradeDate: "2026-01-01" },
      { netValue: 1.2, tradeDate: "2026-01-03" }
    ]
  },
  {
    key: "equal_weight_monthly",
    name: "Equal-weight monthly rebalanced portfolio",
    points: [
      { netValue: 1, tradeDate: "2026-01-01" },
      { netValue: 1.1, tradeDate: "2026-01-02" },
      { netValue: 1.15, tradeDate: "2026-01-03" }
    ]
  },
  {
    key: "csi_300_buy_hold",
    name: "CSI 300 buy-and-hold",
    points: [
      { netValue: 1, tradeDate: "2026-01-01" },
      { netValue: 0.9, tradeDate: "2026-01-02" },
      { netValue: 1.1, tradeDate: "2026-01-03" }
    ]
  }
];

it("returns shared sorted-date x ticks inside the drawable area", () => {
  const geometry = computeMultiEquityCurveGeometry(threeSeriesFixture());

  expect(geometry.dateTicks.map((tick) => tick.value)).toEqual([
    "2026-01-01",
    "2026-01-02",
    "2026-01-03"
  ]);
  const drawableLeft = EQUITY_CURVE_CHART.paddingLeft;
  const drawableRight = EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingRight;
  expect(geometry.dateTicks.map((tick) => tick.x)).toEqual([48, 328, 608]);
  for (const tick of geometry.dateTicks) {
    expect(Number.isFinite(tick.x)).toBe(true);
    expect(tick.x).toBeGreaterThanOrEqual(drawableLeft);
    expect(tick.x).toBeLessThanOrEqual(drawableRight);
  }
});

it("returns finite numeric y ticks spanning the shared value range", () => {
  const geometry = computeMultiEquityCurveGeometry(threeSeriesFixture());

  expect(geometry.valueTicks.length).toBeGreaterThanOrEqual(2);
  expect(geometry.valueTicks[0].value).toBe(0.9);
  expect(geometry.valueTicks[geometry.valueTicks.length - 1].value).toBe(1.2);
  for (const tick of geometry.valueTicks) {
    expect(Number.isFinite(tick.value)).toBe(true);
    expect(tick.value).toBeGreaterThanOrEqual(geometry.minNetValue);
    expect(tick.value).toBeLessThanOrEqual(geometry.maxNetValue);
    expect(tick.y).toBeGreaterThanOrEqual(EQUITY_CURVE_CHART.paddingTop);
    expect(tick.y).toBeLessThanOrEqual(EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom);
  }
});

it("keeps equal-range ticks finite and centered", () => {
  const geometry = computeMultiEquityCurveGeometry([
    {
      key: "strategy",
      name: "Strategy",
      points: [
        { netValue: 1, tradeDate: "2026-01-01" },
        { netValue: 1, tradeDate: "2026-01-02" }
      ]
    }
  ]);

  expect(geometry.minNetValue).toBe(1);
  expect(geometry.maxNetValue).toBe(1);
  expect(geometry.valueTicks).toEqual([{ value: 1, y: 100 }]);
  expect(geometry.series[0].linePath).toBe("M 48.00 100.00 L 608.00 100.00");
});

it("returns first/last endpoint coordinates for every series", () => {
  const geometry = computeMultiEquityCurveGeometry(threeSeriesFixture());

  expect(geometry.series[0].endpoints).toMatchObject({
    first: { x: 48, y: 125.33333333333333 },
    last: { x: 608, y: 24 }
  });
  expect(geometry.series[2].endpoints.first).toMatchObject({ x: 48, y: 125.33333333333333 });
  expect(geometry.series[2].endpoints.last.x).toBe(608);
  for (const item of geometry.series) {
    for (const endpoint of [item.endpoints.first, item.endpoints.last]) {
      expect(Number.isFinite(endpoint.x)).toBe(true);
      expect(Number.isFinite(endpoint.y)).toBe(true);
      expect(endpoint.x).toBeGreaterThanOrEqual(EQUITY_CURVE_CHART.paddingLeft);
      expect(endpoint.x).toBeLessThanOrEqual(EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingRight);
      expect(endpoint.y).toBeGreaterThanOrEqual(EQUITY_CURVE_CHART.paddingTop);
      expect(endpoint.y).toBeLessThanOrEqual(EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom);
    }
  }
});

it("separates converged end-labels deterministically and stays in-bounds", () => {
  const geometry = computeMultiEquityCurveGeometry(threeSeriesFixture());
  const labels = computeSeriesEndLabels(geometry.series);

  expect(labels.map((label) => label.key)).toEqual([
    "strategy",
    "equal_weight_monthly",
    "csi_300_buy_hold"
  ]);
  expect(labels.every((label) => label.x === EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingRight)).toBe(true);

  // Equal endpoint heights would collide; separation pushes them apart.
  const converging = computeMultiEquityCurveGeometry([
    {
      key: "strategy",
      name: "Strategy",
      points: [
        { netValue: 1, tradeDate: "2026-01-01" },
        { netValue: 1, tradeDate: "2026-01-02" }
      ]
    },
    {
      key: "equal_weight_monthly",
      name: "Equal-weight monthly rebalanced portfolio",
      points: [
        { netValue: 1, tradeDate: "2026-01-01" },
        { netValue: 1, tradeDate: "2026-01-02" }
      ]
    },
    {
      key: "csi_300_buy_hold",
      name: "CSI 300 buy-and-hold",
      points: [
        { netValue: 1, tradeDate: "2026-01-01" },
        { netValue: 1, tradeDate: "2026-01-02" }
      ]
    }
  ]);
  const separated = computeSeriesEndLabels(converging.series);
  const yPositions = separated.map((label) => label.y);
  expect(new Set(yPositions).size).toBe(3);

  // Deterministic: same input yields identical output.
  expect(computeSeriesEndLabels(converging.series)).toEqual(separated);

  for (const label of separated) {
    expect(label.y).toBeGreaterThanOrEqual(EQUITY_CURVE_CHART.paddingTop);
    expect(label.y).toBeLessThanOrEqual(EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom);
  }
});

it("keeps end-labels separated and in-bounds when endpoints converge at the bottom edge", () => {
  // Endpoints near the bottom boundary: the separated group would overflow
  // the viewBox, so the whole group shifts up instead of collapsing labels.
  const bottomConverged = computeMultiEquityCurveGeometry([
    {
      key: "strategy",
      name: "Strategy",
      points: [
        { netValue: 1.05, tradeDate: "2026-01-01" },
        { netValue: 1, tradeDate: "2026-01-02" }
      ]
    },
    {
      key: "equal_weight_monthly",
      name: "Equal-weight monthly rebalanced portfolio",
      points: [
        { netValue: 1.05, tradeDate: "2026-01-01" },
        { netValue: 1, tradeDate: "2026-01-02" }
      ]
    },
    {
      key: "csi_300_buy_hold",
      name: "CSI 300 buy-and-hold",
      points: [
        { netValue: 1.05, tradeDate: "2026-01-01" },
        { netValue: 1, tradeDate: "2026-01-02" }
      ]
    }
  ]);
  const labels = computeSeriesEndLabels(bottomConverged.series);

  // Deterministic, non-overlapping, and inside the viewBox.
  expect(computeSeriesEndLabels(bottomConverged.series)).toEqual(labels);
  const yPositions = labels.map((label) => label.y);
  expect(new Set(yPositions).size).toBe(3);
  for (const label of labels) {
    expect(label.y).toBeGreaterThanOrEqual(EQUITY_CURVE_CHART.paddingTop + 4);
    expect(label.y).toBeLessThanOrEqual(EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom - 4);
  }
  expect(Math.max(...yPositions)).toBe(EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom - 4);
});

it("keeps ticks and endpoints finite for an empty multi-series input", () => {
  const geometry = computeMultiEquityCurveGeometry([]);

  expect(geometry.series).toEqual([]);
  expect(geometry.dateTicks).toEqual([]);
  expect(geometry.valueTicks).toEqual([]);
  expect(Number.isFinite(geometry.minNetValue)).toBe(true);
  expect(Number.isFinite(geometry.maxNetValue)).toBe(true);
});
