import { expect, it } from "vitest";
import {
  EMPTY_VALUE,
  formatCompactNumber,
  formatDate,
  formatDecimal,
  formatInteger,
  formatNullableInteger,
  formatNullableText,
  formatRatioAsPercent,
  formatRows,
  formatTargetWeight,
  formatTimestamp
} from "./formatters";

it("formats counts and nullable values consistently", () => {
  expect(formatInteger(1200)).toBe("1,200");
  expect(formatCompactNumber(0.40001)).toBe("0.4");
  expect(formatNullableText(null)).toBe(EMPTY_VALUE);
  expect(formatNullableInteger(null)).toBe(EMPTY_VALUE);
  expect(formatRows(null)).toBe(EMPTY_VALUE);
  expect(formatRows(25)).toBe("25 rows");
});

it("formats dates and timestamps with explicit nullable states", () => {
  expect(formatDate("2026-06-23")).toBe("2026-06-23");
  expect(formatDate("2026-06-23T09:30:00")).toBe("2026-06-23");
  expect(formatDate(null)).toBe(EMPTY_VALUE);
  expect(formatTimestamp("2026-06-23T09:30:00")).toBe("2026-06-23T09:30:00");
  expect(formatTimestamp(null)).toBe(EMPTY_VALUE);
});

it("formats decimal strings, ratios, and target weights", () => {
  expect(formatRatioAsPercent("0.12")).toBe("12.00%");
  expect(formatRatioAsPercent(null)).toBe(EMPTY_VALUE);
  expect(formatTargetWeight("0.333333")).toBe("33.3333%");
  expect(formatTargetWeight("1.000000")).toBe("100%");
  expect(formatDecimal("1.100000", 6)).toBe("1.1");
  expect(formatDecimal("1.1", 2, false)).toBe("1.10");
  expect(formatDecimal(null, 6)).toBe(EMPTY_VALUE);
});
