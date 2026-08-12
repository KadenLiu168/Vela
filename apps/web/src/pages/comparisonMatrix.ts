/**
 * Pure helpers for the strategy-versus-benchmark comparison matrix.
 *
 * Best-value markers are applied ONLY to comparable absolute numeric rows with
 * at least two non-null values. Directions are documented:
 *   - Total return / CAGR / Sharpe / Sortino / Calmar: higher is better.
 *   - Max drawdown: the value closest to zero (numerically greatest; negative
 *     magnitudes are smaller drawdowns).
 *   - Volatility / longest drawdown duration: lower is better.
 * Dates, recovery evidence, relative rows, and distribution/CAPM/capture
 * evidence are never ranked.
 */

export type BestDirection = "higher" | "lower" | "closest-to-zero";

export type ComparisonRow = {
  key: string;
  label: string;
  /** Pre-formatted cell text per entity column (strategy first). */
  cells: string[];
  /** Raw comparable values for best-marker computation; nulls are excluded. */
  numeric?: (number | null)[];
  direction?: BestDirection;
  /** Only absolute numeric rows are rankable. */
  rankable?: boolean;
};

/** Returns the sorted entity-column indexes whose value is "best" under the
 *  documented direction. Requires at least two non-null comparable values. */
export function computeBestCells(
  values: (number | null)[],
  direction: BestDirection
): number[] {
  const present = values.flatMap((value, index) =>
    value === null ? [] : [{ value, index }]
  );
  if (present.length < 2) {
    return [];
  }

  const best =
    direction === "lower"
      ? Math.min(...present.map((entry) => entry.value))
      : Math.max(...present.map((entry) => entry.value));

  return present
    .filter((entry) => entry.value === best)
    .map((entry) => entry.index)
    .sort((a, b) => a - b);
}

export function isRankable(row: ComparisonRow): boolean {
  return row.rankable === true && row.numeric !== undefined;
}

/** Best column indexes for a rankable row, or [] when not rankable. */
export function bestCellIndexes(row: ComparisonRow): number[] {
  if (!isRankable(row) || row.direction === undefined || row.numeric === undefined) {
    return [];
  }
  return computeBestCells(row.numeric, row.direction);
}
