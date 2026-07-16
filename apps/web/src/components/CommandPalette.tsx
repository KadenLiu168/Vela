import { useEffect, useMemo, useRef, useState } from "react";
import type {
  BacktestListResponse,
  DashboardResponse,
  LatestStrategySignalResponse
} from "../api/client";
import { filterCommandRows } from "./commandPaletteFilter";
import type { ActionRow, CommandPaletteRow, PageRow } from "./commandPaletteFilter";

function makeBacktestRow(
  label: string,
  path: string,
  runDate: string,
  id: string
): CommandPaletteRow {
  return {
    kind: "backtest",
    id,
    label,
    path,
    keywords: [runDate],
    runDate
  };
}

function makeEtfRow(
  id: string,
  exchange: string,
  symbol: string,
  category: string | null
): CommandPaletteRow {
  return {
    kind: "etf",
    id,
    label: symbol,
    path: null,
    keywords: [`${exchange}:${symbol}`, category ?? ""],
    exchange,
    symbol,
    category
  };
}

export type CommandPaletteProps = {
  actions: ActionRow[];
  fetchBacktests: () => Promise<BacktestListResponse>;
  fetchDashboard: () => Promise<DashboardResponse>;
  fetchLatestSignal: () => Promise<LatestStrategySignalResponse>;
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (path: string) => void;
  pages: PageRow[];
};

type DataSource = "backtests" | "signals" | "dashboard";

const COMMAND_PALETTE_LISTBOX_ID = "command-palette-listbox";
const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "textarea:not([disabled])",
  "input:not([disabled]):not([type='hidden'])",
  "select:not([disabled])",
  "[tabindex]:not([tabindex='-1'])"
].join(",");

function getCommandPaletteOptionId(rowId: string): string {
  return `command-palette-option-${rowId}`;
}

function getFocusableElements(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(
    (element) => !element.closest("[hidden]") && !element.closest('[aria-hidden="true"]')
  );
}

export function CommandPalette({
  actions,
  fetchBacktests,
  fetchDashboard,
  fetchLatestSignal,
  isOpen,
  onClose,
  onNavigate,
  pages
}: CommandPaletteProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<Element | null>(null);

  // State
  const [query, setQuery] = useState("");
  const [activeRowId, setActiveRowId] = useState<string | null>(null);
  const [expandedEtfId, setExpandedEtfId] = useState<string | null>(null);
  const [loadingSources, setLoadingSources] = useState<Set<DataSource>>(new Set());
  const [errorSources, setErrorSources] = useState<Set<DataSource>>(new Set());
  const [fetchedBacktests, setFetchedBacktests] = useState<CommandPaletteRow[]>([]);
  const [fetchedSignal, setFetchedSignal] = useState<CommandPaletteRow | null>(null);
  const [fetchedEtfs, setFetchedEtfs] = useState<CommandPaletteRow[]>([]);

  // Refs for permanently-bound keydown handler
  const isOpenRef = useRef(isOpen);
  const onCloseRef = useRef(onClose);
  const onNavigateRef = useRef(onNavigate);
  const visibleRowsRef = useRef<CommandPaletteRow[]>([]);
  const expandedEtfIdRef = useRef(expandedEtfId);
  const setExpandedEtfIdRef = useRef(setExpandedEtfId);
  const setActiveRowIdRef = useRef(setActiveRowId);
  const validActiveRowIdRef = useRef<string | null>(null);

  // Sync refs (in effects — satisfies react-hooks/refs rule)
  useEffect(() => { isOpenRef.current = isOpen; }, [isOpen]);
  useEffect(() => { onCloseRef.current = onClose; }, [onClose]);
  useEffect(() => { onNavigateRef.current = onNavigate; }, [onNavigate]);
  useEffect(() => { expandedEtfIdRef.current = expandedEtfId; }, [expandedEtfId]);

  // Open / close lifecycle
  useEffect(() => {
    if (!isOpen) {
      const el = previousActiveElement.current;
      if (el instanceof HTMLElement) {
        requestAnimationFrame(() => {
          el.focus();
        });
      }
      return;
    }

    // Palette just opened — capture focus
    previousActiveElement.current = document.activeElement;
    inputRef.current?.focus();

    // Reset state for fresh open
    /* eslint-disable react-hooks/set-state-in-effect */
    setQuery("");
    setActiveRowId(null);
    setExpandedEtfId(null);
    setFetchedBacktests([]);
    setFetchedSignal(null);
    setFetchedEtfs([]);
    setLoadingSources(new Set(["backtests", "signals", "dashboard"]));
    setErrorSources(new Set());
    /* eslint-enable react-hooks/set-state-in-effect */

    void Promise.allSettled([
      fetchBacktests()
        .then((res) => {
          const rows = (res.runs ?? []).map((run) =>
            makeBacktestRow(
              `Backtest #${run.run_id}`,
              `/backtests/${run.run_id}`,
              run.start_date,
              `backtest-${run.run_id}`
            )
          );
          setFetchedBacktests(rows);
        })
        .catch(() => {
          setErrorSources((prev) => new Set(prev).add("backtests"));
        }),
      fetchLatestSignal()
        .then((res) => {
          if (res.has_signal && res.signal) {
            const row = makeBacktestRow(
              `Signal #${res.signal.signal_id}`,
              `/signals/${res.signal.signal_id}`,
              res.signal.signal_date,
              `signal-${res.signal.signal_id}`
            );
            setFetchedSignal(row);
          }
        })
        .catch(() => {
          setErrorSources((prev) => new Set(prev).add("signals"));
        }),
      fetchDashboard()
        .then((res) => {
          const etfList = res.market_data?.etf_list ?? [];
          const rows = etfList.map((etf) =>
            makeEtfRow(
              `etf-${etf.exchange.toLowerCase()}-${etf.symbol.toLowerCase()}`,
              etf.exchange,
              etf.symbol,
              etf.category ?? null
            )
          );
          setFetchedEtfs(rows);
        })
        .catch(() => {
          setErrorSources((prev) => new Set(prev).add("dashboard"));
        })
    ]).finally(() => {
      setLoadingSources(new Set());
    });
  }, [isOpen, fetchBacktests, fetchLatestSignal, fetchDashboard]);

  // Combine all rows
  const allRows: CommandPaletteRow[] = useMemo(() => {
    return [...pages, ...fetchedBacktests, ...(fetchedSignal ? [fetchedSignal] : []), ...fetchedEtfs, ...actions];
  }, [pages, fetchedBacktests, fetchedSignal, fetchedEtfs, actions]);

  // Filter
  const visibleRows = useMemo(() => filterCommandRows(query, allRows), [query, allRows]);

  // Ensure activeRowId is always valid
  const validActiveRowId: string | null =
    activeRowId && visibleRows.some((r) => r.id === activeRowId)
      ? activeRowId
      : visibleRows.length > 0
        ? visibleRows[0].id
        : null;

  // Sync remaining dynamic refs
  useEffect(() => { visibleRowsRef.current = visibleRows; }, [visibleRows]);
  useEffect(() => { validActiveRowIdRef.current = validActiveRowId; }, [validActiveRowId]);
  useEffect(() => { setActiveRowIdRef.current = setActiveRowId; }, [setActiveRowId]);
  useEffect(() => { setExpandedEtfIdRef.current = setExpandedEtfId; }, [setExpandedEtfId]);

  // Group rows for display
  const groupedRows = useMemo(() => {
    const groups: { kind: CommandPaletteRow["kind"]; label: string; rows: CommandPaletteRow[] }[] = [
      { kind: "page", label: "Pages", rows: [] },
      { kind: "backtest", label: "Backtests", rows: [] },
      { kind: "etf", label: "ETFs", rows: [] },
      { kind: "action", label: "Actions", rows: [] }
    ];

    for (const row of visibleRows) {
      const group = groups.find((g) => g.kind === row.kind);
      if (group) group.rows.push(row);
    }

    return groups.filter((g) => g.rows.length > 0);
  }, [visibleRows]);

  // Row-handler logic used by both keyboard and click
  function commitRow(row: CommandPaletteRow) {
    if (row.kind === "page" || row.kind === "backtest") {
      onNavigateRef.current(row.path);
      onCloseRef.current();
    } else if (row.kind === "action") {
      onCloseRef.current();
      // Defer action so palette closes before async execution
      setTimeout(() => {
        void row.action();
      }, 0);
    } else if (row.kind === "etf") {
      setExpandedEtfIdRef.current((prev: string | null) =>
        prev === row.id ? null : row.id
      );
    }
  }

  // Permanently-bound keydown handler — reads everything from refs
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpenRef.current) return;

      if (e.key === "Escape") {
        e.preventDefault();
        onCloseRef.current();
        return;
      }

      if (e.key === "Tab") {
        const dialog = dialogRef.current;
        if (!dialog) return;

        const focusableElements = getFocusableElements(dialog);
        if (focusableElements.length === 0) {
          e.preventDefault();
          dialog.focus();
          return;
        }

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        const activeElement = document.activeElement;

        if (activeElement === dialog) {
          e.preventDefault();
          if (e.shiftKey) {
            lastElement.focus();
          } else {
            firstElement.focus();
          }
          return;
        }

        if (e.shiftKey && activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
          return;
        }

        if (!e.shiftKey && activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
          return;
        }

        if (!dialog.contains(activeElement)) {
          e.preventDefault();
          firstElement.focus();
          return;
        }
      }

      if (e.key === "ArrowDown") {
        e.preventDefault();
        const rows = visibleRowsRef.current;
        if (rows.length === 0) return;
        const id = validActiveRowIdRef.current;
        const idx = id ? rows.findIndex((r) => r.id === id) : -1;
        const next = idx === -1 || idx >= rows.length - 1 ? 0 : idx + 1;
        setActiveRowIdRef.current(rows[next].id);
        return;
      }

      if (e.key === "ArrowUp") {
        e.preventDefault();
        const rows = visibleRowsRef.current;
        if (rows.length === 0) return;
        const id = validActiveRowIdRef.current;
        const idx = id ? rows.findIndex((r) => r.id === id) : -1;
        const next = idx <= 0 ? rows.length - 1 : idx - 1;
        setActiveRowIdRef.current(rows[next].id);
        return;
      }

      if (e.key === "Enter") {
        e.preventDefault();
        const rows = visibleRowsRef.current;
        if (rows.length === 0) return;
        const id = validActiveRowIdRef.current;
        const activeRow = id ? rows.find((r) => r.id === id) : rows[0];
        if (activeRow) commitRow(activeRow);
        return;
      }

      // Cmd+K / Ctrl+K while open closes it
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        onCloseRef.current();
        return;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (!isOpen) return null;

  const isLoading = loadingSources.size > 0;
  const hasError = errorSources.size > 0;
  const activeDescendantId = validActiveRowId
    ? getCommandPaletteOptionId(validActiveRowId)
    : undefined;

  return (
    <>
      {/* Backdrop */}
      <div
        className="command-palette-backdrop"
        data-testid="command-palette-backdrop"
        onClick={() => onClose()}
        onKeyDown={() => {}}
        role="presentation"
      />
      {/* Dialog */}
      <div
        aria-label="Command palette"
        aria-modal="true"
        className="command-palette-dialog"
        data-testid="command-palette"
        ref={dialogRef}
        role="dialog"
        tabIndex={-1}
      >
        <input
          aria-activedescendant={activeDescendantId}
          aria-controls={visibleRows.length > 0 ? COMMAND_PALETTE_LISTBOX_ID : undefined}
          aria-label="Search"
          autoComplete="off"
          className="command-palette-input"
          data-testid="command-palette-input"
          onChange={(e) => {
            setQuery(e.target.value);
            setActiveRowId(null);
          }}
          placeholder="Search pages, backtests, ETFs, actions…"
          ref={inputRef}
          spellCheck={false}
          type="text"
          value={query}
        />

        {/* Loading indicator */}
        {isLoading ? (
          <div
            className="command-palette-loading"
            data-testid="command-palette-loading"
          >
            Loading data…
          </div>
        ) : null}

        {/* Error rows */}
        {hasError ? (
          <div
            className="command-palette-error"
            data-testid="command-palette-error"
          >
            Failed to load: {[...errorSources].join(", ")}
          </div>
        ) : null}

        {/* Result list */}
        {visibleRows.length > 0 ? (
          <div
            className="command-palette-groups"
            data-testid="command-palette-groups"
            id={COMMAND_PALETTE_LISTBOX_ID}
            role="listbox"
          >
            {groupedRows.map((group) => (
              <div key={group.kind} className="command-palette-group">
                <div className="command-palette-group-header">{group.label}</div>
                {group.rows.map((row) => {
                  const isActive = row.id === validActiveRowId;
                  const isEtfExpanded = row.kind === "etf" && expandedEtfId === row.id;
                  const optionId = getCommandPaletteOptionId(row.id);
                  return (
                    <div key={row.id}>
                      <div
                        aria-selected={isActive}
                        className={`command-palette-row${isActive ? " command-palette-row-active" : ""}`}
                        data-testid={isActive ? "command-palette-row-active" : "command-palette-row"}
                        id={optionId}
                        onClick={() => commitRow(row)}
                        onKeyDown={() => {}}
                        role="option"
                        tabIndex={-1}
                      >
                        <span className="command-palette-row-label">{row.label}</span>
                        <span className="command-palette-row-kind">{row.kind}</span>
                      </div>
                      {/* ETF info panel */}
                      {isEtfExpanded ? (
                        <div
                          className="command-palette-etf-info"
                          data-testid={`command-palette-etf-info-${row.id}`}
                        >
                          {row.kind === "etf" ? (
                            <>
                              <div className="command-palette-etf-info-row">
                                <span>Exchange</span>
                                <strong>{row.exchange}</strong>
                              </div>
                              <div className="command-palette-etf-info-row">
                                <span>Symbol</span>
                                <strong>{row.symbol}</strong>
                              </div>
                              <div className="command-palette-etf-info-row">
                                <span>Category</span>
                                <strong>{row.category ?? "n/a"}</strong>
                              </div>
                              <div className="command-palette-etf-info-row">
                                <span>Name</span>
                                <strong>{row.label}</strong>
                              </div>
                            </>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        ) : (
          /* Empty state */
          <div
            className="command-palette-empty"
            data-testid="command-palette-empty"
          >
            {query.trim()
              ? `No results for "${query.trim()}"`
              : "Type to search…"}
          </div>
        )}
      </div>
    </>
  );
}
