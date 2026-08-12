import { describe, expect, it } from "vitest";
import {
  bestCellIndexes,
  computeBestCells,
  type ComparisonRow
} from "./comparisonMatrix";

describe("computeBestCells", () => {
  it("selects the numerically greatest value for higher-better rows", () => {
    expect(computeBestCells([0.1, 0.08, null], "higher")).toEqual([0]);
    expect(computeBestCells([0.05, 0.1, 0.09], "higher")).toEqual([1]);
  });

  it("selects the numerically smallest value for lower-better rows", () => {
    expect(computeBestCells([0.2, 0.1, null], "lower")).toEqual([1]);
  });

  it("selects the value closest to zero for max drawdown", () => {
    expect(computeBestCells([-0.1, -0.08, null], "closest-to-zero")).toEqual([1]);
    expect(computeBestCells([-0.12, -0.05, -0.09], "closest-to-zero")).toEqual([1]);
  });

  it("marks every tied best cell", () => {
    expect(computeBestCells([0.1, 0.1, 0.05], "higher")).toEqual([0, 1]);
    expect(computeBestCells([-0.1, -0.1, -0.2], "closest-to-zero")).toEqual([0, 1]);
  });

  it("excludes nulls from comparison", () => {
    expect(computeBestCells([null, 0.1, null], "higher")).toEqual([]);
    expect(computeBestCells([0.1, null, 0.1], "higher")).toEqual([0, 2]);
  });

  it("requires at least two non-null comparable values", () => {
    expect(computeBestCells([0.1, null, null], "higher")).toEqual([]);
    expect(computeBestCells([null, null, null], "lower")).toEqual([]);
  });
});

describe("bestCellIndexes", () => {
  const rankableRow = (overrides: Partial<ComparisonRow> = {}): ComparisonRow => ({
    key: "total_return",
    label: "Total return",
    cells: ["10%", "8%", "n/a"],
    numeric: [0.1, 0.08, null],
    direction: "higher",
    rankable: true,
    ...overrides
  });

  it("returns best indexes only for rankable rows", () => {
    expect(bestCellIndexes(rankableRow())).toEqual([0]);
    expect(bestCellIndexes(rankableRow({ rankable: false }))).toEqual([]);
    expect(bestCellIndexes(rankableRow({ numeric: undefined }))).toEqual([]);
    expect(bestCellIndexes(rankableRow({ direction: undefined }))).toEqual([]);
  });

  it("never ranks dates, recovery, or relative evidence rows", () => {
    const dateRow: ComparisonRow = {
      key: "peak_date",
      label: "Longest drawdown peak date",
      cells: ["2026-01-10", "2026-01-12", "n/a"]
    };
    const relativeRow: ComparisonRow = {
      key: "tracking_error",
      label: "Tracking error (252D)",
      cells: ["n/a", "0.038884", "n/a"]
    };
    expect(bestCellIndexes(dateRow)).toEqual([]);
    expect(bestCellIndexes(relativeRow)).toEqual([]);
  });
});
