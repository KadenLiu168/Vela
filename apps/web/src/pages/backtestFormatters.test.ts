import { expect, it } from "vitest";
import { formatEquityCurvePoint, formatParameterSummary } from "./backtestFormatters";

it("formats parameter summaries without changing null, valid, or malformed JSON behavior", () => {
  expect(formatParameterSummary(null)).toBe("n/a");
  expect(formatParameterSummary('{"top_n":2}')).toBe('{\n  "top_n": 2\n}');
  expect(formatParameterSummary("not-json")).toBe("not-json");
});

it("formats composite equity-curve point readouts", () => {
  expect(formatEquityCurvePoint({ netValue: 1.01, tradeDate: "2026-01-02T00:00:00Z" })).toBe(
    "2026-01-02 / 1.0100"
  );
});
