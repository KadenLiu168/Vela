import { expect, it } from "vitest";
import {
  computeEquityCurveGeometry,
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
