import { expect, it } from "vitest";
import { computeTrendGeometry, indexFromX, TREND_CHART, trendDateAxisIndexes } from "./etfTrendChart";

it("clamps nearest hover indexes and chooses stable date-axis indexes", () => {
  expect(indexFromX(-100, 3)).toBe(0);
  expect(indexFromX(56, 3)).toBe(0);
  expect(indexFromX(340, 3)).toBe(1);
  expect(indexFromX(624, 3)).toBe(2);
  expect(indexFromX(9999, 3)).toBe(2);
  expect(indexFromX(197, 3)).toBe(0);
  expect(indexFromX(199, 3)).toBe(1);
  expect(indexFromX(220, 3)).toBe(1);
  expect(trendDateAxisIndexes(2)).toEqual([0, 1]);
  expect(trendDateAxisIndexes(5)).toEqual([0, 2, 4]);
  expect(trendDateAxisIndexes(6)).toEqual([0, 2, 5]);
});

it("keeps normal and equal-price geometry inside the plot bounds", () => {
  const geometry = computeTrendGeometry([{ price: "100" }, { price: "110" }]);
  expect(geometry.linePath).toBe("M 56.00 216.00 L 624.00 16.00");
  expect(geometry.x(0)).toBe(TREND_CHART.paddingLeft);
  expect(geometry.x(1)).toBe(TREND_CHART.width - TREND_CHART.paddingRight);
  expect(geometry.y(100)).toBe(TREND_CHART.height - TREND_CHART.paddingBottom);
  expect(geometry.y(110)).toBe(TREND_CHART.paddingTop);

  const equalGeometry = computeTrendGeometry([{ price: "100" }, { price: "100" }]);
  expect(equalGeometry.linePath).toBe("M 56.00 116.00 L 624.00 116.00");
});
