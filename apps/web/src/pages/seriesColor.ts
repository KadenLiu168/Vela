/**
 * Stable categorical color resolution for multi-series charts.
 *
 * Identity is derived from the series key, never from array position, so a
 * series keeps its token even when another series has no plottable points.
 * The three current supported keys are pinned to explicit tokens; any other
 * key resolves to a deterministic reserved-role fallback (series 4-6) without
 * implying backend support for additional benchmarks.
 */

const SERIES_TOKENS = [
  "var(--color-series-1)",
  "var(--color-series-2)",
  "var(--color-series-3)",
  "var(--color-series-4)",
  "var(--color-series-5)",
  "var(--color-series-6)"
] as const;

export const SERIES_COLOR_BY_KEY: Record<string, string> = {
  strategy: SERIES_TOKENS[0],
  equal_weight_monthly: SERIES_TOKENS[1],
  csi_300_buy_hold: SERIES_TOKENS[2]
};

const RESERVED_ROLE_TOKENS = SERIES_TOKENS.slice(3);

/** Deterministic hash of the key so the same unknown key always lands on the
 *  same reserved role. */
function reservedRoleIndex(key: string): number {
  let sum = 0;
  for (let index = 0; index < key.length; index += 1) {
    sum = (sum + key.charCodeAt(index)) % RESERVED_ROLE_TOKENS.length;
  }
  return sum;
}

export function seriesColor(key: string): string {
  return SERIES_COLOR_BY_KEY[key] ?? RESERVED_ROLE_TOKENS[reservedRoleIndex(key)];
}
