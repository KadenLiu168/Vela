import type { CommandPaletteRow } from "../commandPaletteFilter";

export function makePageRow(
  overrides?: Partial<CommandPaletteRow & { kind: "page" }>
): CommandPaletteRow {
  return {
    kind: "page",
    id: "page-dashboard",
    label: "Dashboard",
    path: "/",
    keywords: ["home", "index"],
    ...overrides
  };
}

export function makeBacktestRow(
  overrides?: Partial<CommandPaletteRow & { kind: "backtest" }>
): CommandPaletteRow {
  return {
    kind: "backtest",
    id: "backtest-7",
    label: "Backtest #7",
    path: "/backtests/7",
    keywords: ["run:7", "2026-01-01"],
    runDate: "2026-01-01",
    ...overrides
  };
}

export function makeEtfRow(
  overrides?: Partial<CommandPaletteRow & { kind: "etf" }>
): CommandPaletteRow {
  return {
    kind: "etf",
    id: "etf-arcx-vti",
    label: "VTI",
    path: null,
    keywords: ["arcx:vti", "equity_us"],
    exchange: "ARCX",
    symbol: "VTI",
    category: "equity_us",
    ...overrides
  };
}

export function makeActionRow(
  overrides?: Partial<CommandPaletteRow & { kind: "action" }>
): CommandPaletteRow {
  return {
    kind: "action",
    id: "action-bootstrap",
    label: "Bootstrap local database",
    path: null,
    keywords: ["setup", "init"],
    action: async () => {},
    ...overrides
  };
}

export const sampleCommandPaletteRows: CommandPaletteRow[] = [
  makePageRow({ id: "page-dashboard", label: "Dashboard", path: "/" }),
  makePageRow({
    id: "page-latest-signal",
    label: "Latest Signal",
    path: "/signals/demo-signal",
    keywords: ["demo"]
  }),
  makePageRow({ id: "page-backtests", label: "Backtest Detail", path: "/backtests" }),
  makeBacktestRow({ id: "backtest-7", label: "Backtest #7", runDate: "2026-01-01" }),
  makeBacktestRow({ id: "backtest-8", label: "Backtest #8", runDate: "2026-02-01" }),
  makeEtfRow({
    id: "etf-arcx-vti",
    label: "VTI",
    symbol: "VTI",
    exchange: "ARCX",
    category: "equity_us"
  }),
  makeEtfRow({
    id: "etf-nasdaq-qqq",
    label: "QQQ",
    symbol: "QQQ",
    exchange: "NASDAQ",
    category: "equity_us_tech"
  }),
  makeActionRow({ id: "action-bootstrap", label: "Bootstrap local database" }),
  makeActionRow({ id: "action-generate-signal", label: "Generate strategy signal" }),
  makeActionRow({ id: "action-run-backtest", label: "Run backtest" })
];
