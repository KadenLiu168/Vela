import type { StoryDefault } from "@ladle/react";
import { CommandPalette } from "./CommandPalette";
import type { CommandPaletteProps } from "./CommandPalette";
import { sampleCommandPaletteRows } from "./__fixtures__/commandPaletteFixtures";
import type {
  BacktestListResponse,
  DashboardMarketDataStatus,
  DashboardResponse,
  LatestStrategySignalResponse
} from "../api/client";
import type { CommandPaletteRow } from "./commandPaletteFilter";

/** Minimal DashboardResponse for Ladle stories. */
function dashboardWithEtfs(etf_list: DashboardMarketDataStatus["etf_list"]): DashboardResponse {
  return {
    strategy: {
      strategy_id: "",
      version: "",
      universe_config: "",
      momentum: { short_window_days: 0, long_window_days: 0 },
      score_weights: { short: 0, long: 0 },
      trend_filter: {},
      selection: { top_n: 0 },
      defense: { asset: { exchange: "", symbol: "" } },
      costs: { transaction_cost_bps: 0 },
      performance: {},
      rebalance: { frequency: "" }
    },
    market_data: {
      price_rows: 0,
      covered_etfs: etf_list.length,
      earliest_trade_date: null,
      latest_trade_date: null,
      etf_list
    },
    latest_signal: null,
    recent_backtest: null,
    recent_fetch_logs: []
  };
}

// Extract typed rows from fixtures
const pageRows = sampleCommandPaletteRows.filter(
  (r): r is CommandPaletteRow & { kind: "page" } => r.kind === "page"
);
const actionRows = sampleCommandPaletteRows.filter(
  (r): r is CommandPaletteRow & { kind: "action" } => r.kind === "action"
);
const backtestRows = sampleCommandPaletteRows.filter(
  (r): r is CommandPaletteRow & { kind: "backtest" } => r.kind === "backtest"
);
const etfRows = sampleCommandPaletteRows.filter(
  (r): r is CommandPaletteRow & { kind: "etf" } => r.kind === "etf"
);

function resolved<T>(data: T): () => Promise<T> {
  return () => Promise.resolve(data);
}

function rejected<T>(error: Error): () => Promise<T> {
  return () => Promise.reject(error);
}

const defaultProps: CommandPaletteProps = {
  actions: actionRows,
  fetchBacktests: resolved({
    runs: backtestRows.map((r) => ({
      run_id: parseInt(r.id.replace("backtest-", ""), 10),
      strategy_id: "dual_momentum",
      config_version: "v1",
      start_date: r.runDate,
      end_date: r.runDate,
      status: "success",
      started_at: `${r.runDate}T09:00:00`,
      finished_at: null,
      total_return: null,
      annualized_return: null,
      max_drawdown: null,
      volatility: null,
      sharpe_ratio: null
    }))
  } satisfies BacktestListResponse),
  fetchDashboard: resolved(
    dashboardWithEtfs(
      etfRows.map((r) => ({
        exchange: r.exchange,
        symbol: r.symbol,
        name: r.label,
        category: r.category,
        earliest_trade_date: null,
      }))
    )
  ),
  fetchLatestSignal: resolved({
    has_signal: false,
    signal: null,
    positions: []
  } satisfies LatestStrategySignalResponse),
  isOpen: true,
  onClose: () => {},
  onNavigate: () => {},
  pages: pageRows
};

export default {
  title: "CommandPalette"
} satisfies StoryDefault;

// ── Stories ─────────────────────────────────────────────────────────────────

export function Closed() {
  return (
    <CommandPalette {...defaultProps} isOpen={false} />
  );
}

Closed.storyName = "Closed";

export function OpenWithNoQuery() {
  return (
    <CommandPalette
      {...defaultProps}
      fetchBacktests={resolved({ runs: [] } satisfies BacktestListResponse)}
      fetchDashboard={resolved(dashboardWithEtfs([]))}
    />
  );
}

OpenWithNoQuery.storyName = "OpenWithNoQuery";

export function OpenWithBacktestsLoaded() {
  return (
    <CommandPalette
      {...defaultProps}
      fetchLatestSignal={resolved({
        has_signal: true,
        signal: {
          signal_id: 7,
          signal_date: "2026-01-01",
          config_version: "v1",
          result: "rebalance",
          generated_at: "2026-01-01T09:00:00",
          is_fallback: false
        },
        positions: []
      } satisfies LatestStrategySignalResponse)}
    />
  );
}

OpenWithBacktestsLoaded.storyName = "OpenWithBacktestsLoaded";

export function OpenWithEtfsLoaded() {
  return (
    <CommandPalette {...defaultProps} />
  );
}

OpenWithEtfsLoaded.storyName = "OpenWithEtfsLoaded";

export function OpenWithError() {
  return (
    <CommandPalette
      {...defaultProps}
      fetchBacktests={rejected(new Error("API unavailable"))}
    />
  );
}

OpenWithError.storyName = "OpenWithError";

export function OpenWithSelectedEtfInfo() {
  return (
    <CommandPalette {...defaultProps} />
  );
}

OpenWithSelectedEtfInfo.storyName = "OpenWithSelectedEtfInfo";
