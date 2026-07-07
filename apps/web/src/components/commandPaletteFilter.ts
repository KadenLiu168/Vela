/** Discriminated union for rows surfaced by the command palette. */
export type PageRow = {
  kind: "page";
  id: string;
  label: string;
  path: string;
  keywords: string[];
};

export type BacktestRow = {
  kind: "backtest";
  id: string;
  label: string;
  path: string;
  keywords: string[];
  runDate: string;
};

export type EtfRow = {
  kind: "etf";
  id: string;
  label: string;
  path: null;
  keywords: string[];
  exchange: string;
  symbol: string;
  category: string | null;
};

export type ActionRow = {
  kind: "action";
  id: string;
  label: string;
  path: null;
  keywords: string[];
  action: () => void | Promise<void>;
};

export type CommandPaletteRow = PageRow | BacktestRow | EtfRow | ActionRow;

/** Group display order — Pages, Backtests, ETFs, Actions. */
const GROUP_ORDER: CommandPaletteRow["kind"][] = ["page", "backtest", "etf", "action"];

function getGroupOrder(row: CommandPaletteRow): number {
  return GROUP_ORDER.indexOf(row.kind);
}

const EMPTY_QUERY_RESULT_CAP = 20;
const NON_EMPTY_QUERY_RESULT_CAP = 50;

/**
 * Pure helper that filters and sorts command palette rows.
 *
 * Algorithm (per spec):
 * - Empty / whitespace query → return pages + actions only, capped at 20.
 * - Non-empty query → case-insensitive substring match on `label` (always)
 *   and `keywords` (when present). Label-hit rows sort before keyword-hit rows.
 * - Within each match band: group-stable (Pages → Backtests → ETFs → Actions),
 *   then alphabetical by label.
 * - Results capped at 50.
 */
export function filterCommandRows(
  query: string,
  rows: CommandPaletteRow[]
): CommandPaletteRow[] {
  const trimmed = query.trim();

  if (trimmed.length === 0) {
    return rows
      .filter((row) => row.kind === "page" || row.kind === "action")
      .slice(0, EMPTY_QUERY_RESULT_CAP);
  }

  const lowerQuery = trimmed.toLowerCase();

  type ScoredRow = { row: CommandPaletteRow; isLabelMatch: boolean };

  const scored: ScoredRow[] = [];

  for (const row of rows) {
    const labelMatch = row.label.toLowerCase().includes(lowerQuery);
    const keywordMatch = row.keywords.some((kw) =>
      kw.toLowerCase().includes(lowerQuery)
    );

    if (labelMatch) {
      scored.push({ row, isLabelMatch: true });
    } else if (keywordMatch) {
      scored.push({ row, isLabelMatch: false });
    }
  }

  // Sort: label-hit first, then group-stable order, then alphabetical by label
  scored.sort((a, b) => {
    // Label hits before keyword hits
    if (a.isLabelMatch !== b.isLabelMatch) {
      return a.isLabelMatch ? -1 : 1;
    }

    // Group-stable: same match band keeps group order
    const groupCmp = getGroupOrder(a.row) - getGroupOrder(b.row);
    if (groupCmp !== 0) return groupCmp;

    // Alphabetical by label within the same group
    return a.row.label.localeCompare(b.row.label);
  });

  return scored.slice(0, NON_EMPTY_QUERY_RESULT_CAP).map((s) => s.row);
}
