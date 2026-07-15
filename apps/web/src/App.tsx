import { useCallback, useEffect, useRef, useState } from "react";
import {
  type ActionRow,
  type PageRow,
  CommandPalette
} from "./components";
import {
  getApiBaseUrl,
  getDashboard,
  getLatestStrategySignal,
  listBacktests,
  runBacktest,
  bootstrapLocalDatabase,
  generateStrategySignal
} from "./api/client";
import { type NavItem, AppShell } from "./components/AppShell";
import { ErrorBoundary } from "./components";
import { BacktestDetailPage } from "./pages/BacktestDetailPage";
import { BacktestListPage } from "./pages/BacktestListPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EtfDetailPage } from "./pages/EtfDetailPage";
import { SignalDetailPage } from "./pages/SignalDetailPage";
import { SignalListPage } from "./pages/SignalListPage";

const navItems: NavItem[] = [
  { href: "/", label: "Dashboard" },
  { href: "/signals", label: "Signals" },
  { href: "/backtests", label: "Backtests" }
];

const pageRows: PageRow[] = navItems.map((item) => ({
  kind: "page" as const,
  id: `page-${item.href === "/" ? "dashboard" : item.href.replace(/^\//, "").replace(/\//g, "-")}`,
  label: item.label,
  path: item.href,
  keywords: []
}));

export default function App() {
  const [path, setPath] = useState(getCurrentPath);
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);
  const isPaletteOpenRef = useRef(isPaletteOpen);

  // Lifted backtest form state from DashboardPage
  const [backtestStartDate, setBacktestStartDate] = useState("");
  const [backtestEndDate, setBacktestEndDate] = useState("");
  const backtestStartDateRef = useRef(backtestStartDate);
  const backtestEndDateRef = useRef(backtestEndDate);

  useEffect(() => {
    backtestStartDateRef.current = backtestStartDate;
  }, [backtestStartDate]);

  useEffect(() => {
    backtestEndDateRef.current = backtestEndDate;
  }, [backtestEndDate]);

  useEffect(() => {
    isPaletteOpenRef.current = isPaletteOpen;
  }, [isPaletteOpen]);

  useEffect(() => {
    const handlePopState = () => {
      setPath(getCurrentPath());
    };

    window.addEventListener("popstate", handlePopState);

    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  // Global keydown: open palette via Cmd+K / Ctrl+K / /
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const isFormInput =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement ||
        target?.isContentEditable;

      // Cmd+K / Ctrl+K — toggle palette
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsPaletteOpen((prev) => !prev);
        return;
      }

      // Slash — open palette when not in a form input
      if (!isFormInput && e.key === "/" && !isPaletteOpenRef.current) {
        e.preventDefault();
        setIsPaletteOpen(true);
        return;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const navigate = (nextPath: string) => {
    if (nextPath !== getCurrentPath()) {
      window.history.pushState({}, "", nextPath);
    }

    setPath(nextPath);
  };

  // Actions for the command palette
  const [paletteActions] = useState<ActionRow[]>(() => [
    {
      kind: "action",
      id: "action-bootstrap",
      label: "Bootstrap local database",
      path: null,
      keywords: ["setup", "init"],
      action: async () => {
        await bootstrapLocalDatabase();
      }
    },
    {
      kind: "action",
      id: "action-generate-signal",
      label: "Generate strategy signal",
      path: null,
      keywords: ["signal"],
      action: async () => {
        await generateStrategySignal();
      }
    },
    {
      kind: "action",
      id: "action-run-backtest",
      label: "Run backtest",
      path: null,
      keywords: ["backtest", "run"],
      action: async () => {
        await runBacktest(backtestStartDateRef.current, backtestEndDateRef.current);
      }
    }
  ]);

  // Stable fetch callbacks to avoid re-triggering CommandPalette's data effect
  const fetchBacktestsCb = useCallback(() => listBacktests(10), []);
  const fetchDashboardCb = useCallback(() => getDashboard(), []);
  const fetchLatestSignalCb = useCallback(() => getLatestStrategySignal(), []);

  return (
    <AppShell
      activePath={getActivePath(path)}
      apiBaseUrl={getApiBaseUrl()}
      commandPalette={
        <CommandPalette
          actions={paletteActions}
          fetchBacktests={fetchBacktestsCb}
          fetchDashboard={fetchDashboardCb}
          fetchLatestSignal={fetchLatestSignalCb}
          isOpen={isPaletteOpen}
          onClose={() => setIsPaletteOpen(false)}
          onNavigate={navigate}
          pages={pageRows}
        />
      }
      navItems={navItems}
      onNavigate={navigate}
    >
      <ErrorBoundary>{renderRoute(path, backtestStartDate, backtestEndDate, setBacktestStartDate, setBacktestEndDate)}</ErrorBoundary>
    </AppShell>
  );
}

function renderRoute(
  path: string,
  backtestStartDate?: string,
  backtestEndDate?: string,
  setBacktestStartDate?: (value: string) => void,
  setBacktestEndDate?: (value: string) => void
) {
  if (path === "/signals") {
    return <SignalListPage />;
  }

  const signalMatch = path.match(/^\/signals\/(\d+)$/);

  if (signalMatch) {
    return <SignalDetailPage signalId={signalMatch[1]} />;
  }

  if (path === "/backtests") {
    return <BacktestListPage />;
  }

  const backtestMatch = path.match(/^\/backtests\/(\d+)$/);

  if (backtestMatch) {
    return <BacktestDetailPage backtestId={backtestMatch[1]} />;
  }

  const etfMatch = path.match(/^\/etfs\/(\d+)$/);

  if (etfMatch) {
    return <EtfDetailPage etfId={etfMatch[1]} />;
  }

  return (
    <DashboardPage
      backtestForm={{ startDate: backtestStartDate ?? "", endDate: backtestEndDate ?? "" }}
      onBacktestFormChange={
        setBacktestStartDate && setBacktestEndDate
          ? (form) => {
              setBacktestStartDate(form.startDate);
              setBacktestEndDate(form.endDate);
            }
          : undefined
      }
    />
  );
}

function getActivePath(path: string): string {
  if (path === "/signals" || path.startsWith("/signals/")) {
    return "/signals";
  }

  if (path === "/backtests" || path.startsWith("/backtests/")) {
    return "/backtests";
  }

  if (path === "/etfs" || path.startsWith("/etfs/")) {
    return "/etfs";
  }

  return "/";
}

function getCurrentPath(): string {
  return window.location.pathname;
}
