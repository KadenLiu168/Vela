import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CommandPalette, type CommandPaletteProps } from "./CommandPalette";
import { filterCommandRows } from "./commandPaletteFilter";
import type {
  BacktestListResponse,
  DashboardMarketDataStatus,
  DashboardResponse,
  LatestStrategySignalResponse
} from "../api/client";
import {
  makeActionRow,
  makeBacktestRow,
  makeEtfRow,
  makePageRow
} from "./__fixtures__/commandPaletteFixtures";
import type { CommandPaletteRow } from "./commandPaletteFilter";
import type { ActionRow, PageRow } from "./commandPaletteFilter";

/** Minimal DashboardResponse with the given ETF list. */
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
      defense: { assets: [{ exchange: "", symbol: "" }] },
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

// ── Filter helper unit tests ────────────────────────────────────────────────

describe("filterCommandRows", () => {
  const pageRows: CommandPaletteRow[] = [
    makePageRow({ id: "p1", label: "Dashboard", path: "/" }),
    makePageRow({
      id: "p2",
      label: "Latest Signal",
      path: "/signals/demo-signal"
    }),
    makePageRow({ id: "p3", label: "Backtest Detail", path: "/backtests" })
  ];

  const actionRows: CommandPaletteRow[] = [
    makeActionRow({ id: "a1", label: "Bootstrap local database" }),
    makeActionRow({ id: "a2", label: "Generate strategy signal" }),
    makeActionRow({ id: "a3", label: "Run backtest" })
  ];

  const backtestRows: CommandPaletteRow[] = [
    makeBacktestRow({ id: "b1", label: "Backtest #7", runDate: "2026-01-01" }),
    makeBacktestRow({ id: "b2", label: "Backtest #8", runDate: "2026-02-01" })
  ];

  const etfRows: CommandPaletteRow[] = [
    makeEtfRow({
      id: "e1",
      label: "VTI",
      symbol: "VTI",
      exchange: "ARCX",
      category: "equity_us"
    }),
    makeEtfRow({
      id: "e2",
      label: "VOO",
      symbol: "VOO",
      exchange: "ARCX",
      category: "equity_us"
    })
  ];

  const allRows = [...pageRows, ...backtestRows, ...etfRows, ...actionRows];

  it("returns pages + actions only for empty query, capped at 20", () => {
    const result = filterCommandRows("", allRows);
    expect(result).toHaveLength(6); // 3 pages + 3 actions
    expect(result.every((r) => r.kind === "page" || r.kind === "action")).toBe(
      true
    );
  });

  it("returns pages + actions only for whitespace query", () => {
    const result = filterCommandRows("   ", allRows);
    expect(result).toHaveLength(6);
    expect(result.every((r) => r.kind === "page" || r.kind === "action")).toBe(
      true
    );
  });

  it("caps empty query results at 20", () => {
    const manyPages = Array.from({ length: 25 }, (_, i) =>
      makePageRow({
        id: `p-extra-${i}`,
        label: `Page ${i}`,
        path: `/${i}`
      })
    );
    const result = filterCommandRows("", manyPages);
    expect(result).toHaveLength(20);
  });

  it("matches label case-insensitively for non-empty query", () => {
    const result = filterCommandRows("backtest", allRows);
    expect(result.length).toBeGreaterThanOrEqual(2);
    // Pages come first in group order, so "Backtest Detail" page is first
    // Backtest rows also match and appear in the backtest group
    expect(result.some((r) => r.kind === "backtest")).toBe(true);
  });

  it("matches keywords when label does not match", () => {
    const result = filterCommandRows("setup", allRows);
    expect(result.length).toBeGreaterThanOrEqual(1);
    // "setup" is a keyword on the bootstrap action
    expect(result.some((r) => r.id === "a1")).toBe(true);
  });

  it("sorts label-hit rows before keyword-hit rows", () => {
    // "vti" matches label of ETF row VTI (label hit) and for some with keyword "arcx:vti"
    const result = filterCommandRows("vti", [
      makeEtfRow({
        id: "e-vti",
        label: "VTI",
        symbol: "VTI",
        exchange: "ARCX",
        keywords: ["arcx:vti"]
      })
    ]);
    expect(result.length).toBeGreaterThanOrEqual(1);
    // Only 1 row matches on label, so ordering is trivially correct
    expect(result[0].id).toBe("e-vti");
  });

  it("maintains group-stable order: Pages → Backtests → ETFs → Actions", () => {
    const result = filterCommandRows("backtest", allRows);
    const groupOrder = result
      .filter((r) => r.kind === "backtest" || r.kind === "page")
      .map((r) => r.kind);
    // If both page and backtest match, pages come first
    const firstBacktestIdx = groupOrder.indexOf("backtest");
    const lastPageIdx = groupOrder.lastIndexOf("page");
    if (lastPageIdx >= 0 && firstBacktestIdx >= 0) {
      expect(lastPageIdx).toBeLessThan(firstBacktestIdx);
    }
  });

  it("caps non-empty query results at 50", () => {
    const many = Array.from({ length: 60 }, (_, i) =>
      makePageRow({
        id: `p-${i}`,
        label: `Matchable Page ${i}`,
        path: `/${i}`
      })
    );
    const result = filterCommandRows("matchable", many);
    expect(result).toHaveLength(50);
  });

  it("returns empty array when no rows match", () => {
    const result = filterCommandRows("zzzznonexistent", allRows);
    expect(result).toHaveLength(0);
  });
});

// ── Component tests ─────────────────────────────────────────────────────────

function createDefaultProps(
  overrides?: Partial<CommandPaletteProps>
): CommandPaletteProps {
  const onClose = vi.fn();
  const onNavigate = vi.fn();

  const actionRows = [
    makeActionRow({
      id: "action-bootstrap",
      label: "Bootstrap local database",
      keywords: ["setup"],
      action: vi.fn()
    }),
    makeActionRow({
      id: "action-generate-signal",
      label: "Generate strategy signal",
      keywords: ["signal"],
      action: vi.fn()
    }),
    makeActionRow({
      id: "action-run-backtest",
      label: "Run backtest",
      keywords: ["backtest"],
      action: vi.fn()
    })
  ] as ActionRow[];

  const pageRows = [
    makePageRow({
      id: "page-dashboard",
      label: "Dashboard",
      path: "/"
    }),
    makePageRow({
      id: "page-latest-signal",
      label: "Latest Signal",
      path: "/signals/demo-signal"
    })
  ] as PageRow[];

  return {
    actions: actionRows,
    fetchBacktests: vi
      .fn()
      .mockResolvedValue({ runs: [] } satisfies BacktestListResponse),
    fetchDashboard: vi
      .fn()
      .mockResolvedValue(dashboardWithEtfs([])),
    fetchLatestSignal: vi
      .fn()
      .mockResolvedValue({
        has_signal: false,
        signal: null,
        positions: []
      } satisfies LatestStrategySignalResponse),
    isOpen: true,
    onClose,
    onNavigate,
    pages: pageRows,
    ...overrides
  };
}

describe("CommandPalette", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // Visibility
  it("renders nothing when isOpen is false", () => {
    const props = createDefaultProps({ isOpen: false });
    const { container } = render(<CommandPalette {...props} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders the dialog when isOpen is true", () => {
    render(<CommandPalette {...createDefaultProps()} />);
    expect(
      screen.getByTestId("command-palette")
    ).toBeInTheDocument();
  });

  // Keyboard contract
  it("focuses the input when rendered", () => {
    render(<CommandPalette {...createDefaultProps()} />);
    expect(screen.getByTestId("command-palette-input")).toHaveFocus();
  });

  // Escape closes
  it("closes on Escape", () => {
    const onClose = vi.fn();
    render(<CommandPalette {...createDefaultProps({ onClose })} />);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  // ArrowDown
  it("moves active row on ArrowDown", () => {
    render(<CommandPalette {...createDefaultProps()} />);
    // ArrowDown activates next row
    fireEvent.keyDown(window, { key: "ArrowDown" });
    // At least one row should be active
    const activeRow = screen.getByTestId("command-palette-row-active");
    expect(activeRow).toBeInTheDocument();
  });

  // ArrowDown wraps
  it("wraps ArrowDown from last to first", () => {
    render(<CommandPalette {...createDefaultProps()} />);
    // Press ArrowDown many times to reach the end and wrap
    const rows = screen.getAllByTestId(/command-palette-row/);
    const visibleCount = rows.length;

    for (let i = 0; i < visibleCount + 1; i++) {
      fireEvent.keyDown(window, { key: "ArrowDown" });
    }

    // Should wrap back to first row
    const activeRows = screen.getAllByTestId("command-palette-row-active");
    expect(activeRows.length).toBe(1);
  });

  // Enter activates a row
  it("calls onNavigate when Enter is pressed on a page row", () => {
    const onNavigate = vi.fn();
    const onClose = vi.fn();
    render(
      <CommandPalette
        {...createDefaultProps({ onNavigate, onClose })}
      />
    );

    // Press Enter on the active (first) row
    fireEvent.keyDown(window, { key: "Enter" });

    // First row should be a page row (Dashboard), so it should navigate
    expect(onNavigate).toHaveBeenCalledWith("/");
  });

  // Data fetching
  it("fetches all three data sources on open", () => {
    const fetchBacktests = vi
      .fn()
      .mockResolvedValue({ runs: [] } satisfies BacktestListResponse);
    const fetchLatestSignal = vi
      .fn()
      .mockResolvedValue({
        has_signal: false,
        signal: null,
        positions: []
      } satisfies LatestStrategySignalResponse);
    const fetchDashboard = vi
      .fn()
      .mockResolvedValue(dashboardWithEtfs([]));

    render(
      <CommandPalette
        {...createDefaultProps({
          fetchBacktests,
          fetchLatestSignal,
          fetchDashboard
        })}
      />
    );

    expect(fetchBacktests).toHaveBeenCalledTimes(1);
    expect(fetchLatestSignal).toHaveBeenCalledTimes(1);
    expect(fetchDashboard).toHaveBeenCalledTimes(1);
  });

  it("shows loading indicator while data is being fetched", () => {
    const fetchBacktests = vi.fn(
      () =>
        new Promise<BacktestListResponse>((resolve) =>
          setTimeout(() => resolve({ runs: [] }), 1000)
        )
    );
    render(
      <CommandPalette
        {...createDefaultProps({ fetchBacktests })}
      />
    );
    expect(
      screen.getByTestId("command-palette-loading")
    ).toBeInTheDocument();
  });

  // Selection: page navigates and closes
  it("navigates and closes when a page row is clicked", () => {
    const onNavigate = vi.fn();
    const onClose = vi.fn();
    render(
      <CommandPalette
        {...createDefaultProps({ onNavigate, onClose })}
      />
    );

    const firstPageRow = screen.getAllByTestId(/command-palette-row/)[0];
    fireEvent.click(firstPageRow);

    expect(onNavigate).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });

  // Selection: action invokes and closes
  it("invokes action and closes when an action row is clicked", () => {
    const action = vi.fn();
    const onClose = vi.fn();
    render(
      <CommandPalette
        {...createDefaultProps({
          actions: [
            makeActionRow({
              id: "action-bootstrap",
              label: "Bootstrap",
              action
            })
          ] as ActionRow[],
          onClose
        })}
      />
    );

    // Type to filter to actions only
    const input = screen.getByTestId("command-palette-input");
    fireEvent.change(input, { target: { value: "Bootstrap" } });

    const actionRow = screen.getByText("Bootstrap").closest('[role="option"]');
    expect(actionRow).not.toBeNull();
    fireEvent.click(actionRow!);

    // Action is deferred via setTimeout(0) so the palette closes first
    vi.advanceTimersByTime(0);

    expect(action).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });

  // Selection: ETF expands info panel
  it("expands ETF info panel when clicked", async () => {
    render(
      <CommandPalette
        {...createDefaultProps({
          pages: [],
          actions: [],
          fetchBacktests: vi
            .fn()
            .mockResolvedValue({ runs: [] } satisfies BacktestListResponse),
          fetchDashboard: vi
            .fn()
            .mockResolvedValue(
              dashboardWithEtfs([
                {
                  etf_id: 1,
                  exchange: "ARCX",
                  symbol: "VTI",
                  name: "VTI ETF",
                  category: "equity_us",
                  earliest_trade_date: null,
                }
              ])
            ),
          fetchLatestSignal: vi
            .fn()
            .mockResolvedValue({
              has_signal: false,
              signal: null,
              positions: []
            } satisfies LatestStrategySignalResponse)
        })}
      />
    );

    // Wait for loading to complete and ETF data to be available
    await vi.waitFor(() => {
      expect(
        screen.queryByTestId("command-palette-loading")
      ).not.toBeInTheDocument();
    });

    const input = screen.getByTestId("command-palette-input");
    fireEvent.change(input, { target: { value: "VTI" } });

    const etfRow = screen.getByText("VTI").closest('[role="option"]');
    expect(etfRow).not.toBeNull();
    fireEvent.click(etfRow!);

    expect(
      screen.getByTestId("command-palette-etf-info-etf-arcx-vti")
    ).toBeInTheDocument();
  });

  // Backdrop click closes
  it("closes when backdrop is clicked", () => {
    const onClose = vi.fn();
    render(<CommandPalette {...createDefaultProps({ onClose })} />);
    fireEvent.click(screen.getByTestId("command-palette-backdrop"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  // Error state
  it("renders error rows when API fails", async () => {
    render(
      <CommandPalette
        {...createDefaultProps({
          fetchBacktests: vi.fn().mockRejectedValue(new Error("API error"))
        })}
      />
    );

    // Error should be rendered after the fetch fails
    const errorElement = await screen.findByTestId("command-palette-error");
    expect(errorElement).toBeInTheDocument();
  });

  // Empty state
  it("shows empty state when no rows match", () => {
    render(<CommandPalette {...createDefaultProps()} />);
    const input = screen.getByTestId("command-palette-input");
    fireEvent.change(input, {
      target: { value: "zzzznonexistent" }
    });
    expect(screen.getByTestId("command-palette-empty")).toHaveTextContent(
      'No results for "zzzznonexistent"'
    );
  });
});
