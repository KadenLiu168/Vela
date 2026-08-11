import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import {
  BrowserRouter,
  Link,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams
} from "react-router-dom";
import { CommandPalette } from "./components/CommandPalette";
import type { ActionRow, PageRow } from "./components/commandPaletteFilter";
import {
  getApiBaseUrl,
  getDashboard,
  getLatestStrategySignal,
  listBacktests,
  runBacktest,
  runWalkForward,
  bootstrapLocalDatabase,
  generateStrategySignal
} from "./api/client";
import { type NavItem, AppShell } from "./components/AppShell";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Skeleton } from "./components/Skeleton";
import { DashboardPage } from "./pages/DashboardPage";

const SignalListPage = lazy(async () => {
  const module = await import("./pages/SignalListPage");
  return { default: module.SignalListPage };
});
const SignalDetailPage = lazy(async () => {
  const module = await import("./pages/SignalDetailPage");
  return { default: module.SignalDetailPage };
});
const BacktestListPage = lazy(async () => {
  const module = await import("./pages/BacktestListPage");
  return { default: module.BacktestListPage };
});
const BacktestDetailPage = lazy(async () => {
  const module = await import("./pages/BacktestDetailPage");
  return { default: module.BacktestDetailPage };
});
const EtfDetailPage = lazy(async () => {
  const module = await import("./pages/EtfDetailPage");
  return { default: module.EtfDetailPage };
});
const WalkForwardListPage = lazy(async () => {
  const module = await import("./pages/WalkForwardListPage");
  return { default: module.WalkForwardListPage };
});
const WalkForwardDetailPage = lazy(async () => {
  const module = await import("./pages/WalkForwardDetailPage");
  return { default: module.WalkForwardDetailPage };
});

const navItems: NavItem[] = [
  { href: "/", label: "Dashboard" },
  { href: "/signals", label: "Signals" },
  { href: "/backtests", label: "Backtests" },
  { href: "/walk-forwards", label: "Walk-forwards" }
];

const pageRows: PageRow[] = navItems.map((item) => ({
  kind: "page" as const,
  id: `page-${item.href === "/" ? "dashboard" : item.href.replace(/^\//, "").replace(/\//g, "-")}`,
  label: item.label,
  path: item.href,
  keywords: []
}));

const DECIMAL_ID = /^\d+$/;

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

function AppContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);

  // Lifted backtest form state from DashboardPage
  const [backtestStartDate, setBacktestStartDate] = useState("");
  const [backtestEndDate, setBacktestEndDate] = useState("");
  const backtestStartDateRef = useRef(backtestStartDate);
  const backtestEndDateRef = useRef(backtestEndDate);

  // Global keydown: open palette via Cmd+K / Ctrl+K / /
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const isFormInput =
        target?.matches?.("input, textarea, select") ||
        target?.isContentEditable;

      // Cmd+K / Ctrl+K — toggle palette
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsPaletteOpen((prev) => !prev);
        return;
      }

      // Slash — open palette when not in a form input
      if (!isFormInput && e.key === "/" && !isPaletteOpen) {
        e.preventDefault();
        setIsPaletteOpen(true);
        return;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isPaletteOpen]);

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
    },
    {
      kind: "action",
      id: "action-run-walk-forward",
      label: "Run walk-forward",
      path: null,
      keywords: ["walk-forward", "walk", "wf", "run"],
      action: async () => {
        const accepted = await runWalkForward();
        navigate(`/walk-forwards/${accepted.walk_forward_run_id}`);
      }
    }
  ]);

  // Stable fetch callbacks to avoid re-triggering CommandPalette's data effect
  const fetchBacktestsCb = useCallback(() => listBacktests(10), []);
  const fetchDashboardCb = useCallback(() => getDashboard(), []);
  const fetchLatestSignalCb = useCallback(() => getLatestStrategySignal(), []);

  return (
    <AppShell
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
    >
      <ErrorBoundary key={location.pathname} fallback={<RouteLoadFailureFallback />}>
        <Suspense fallback={<RouteLoadingFallback />}>
          <Routes>
            <Route
              path="/"
              element={
                <DashboardPage
                  backtestForm={{ startDate: backtestStartDate, endDate: backtestEndDate }}
                  onBacktestFormChange={(form) => {
                    backtestStartDateRef.current = form.startDate;
                    backtestEndDateRef.current = form.endDate;
                    setBacktestStartDate(form.startDate);
                    setBacktestEndDate(form.endDate);
                  }}
                />
              }
            />
            <Route path="/signals" element={<SignalListPage />} />
            <Route path="/signals/:signalId" element={<SignalDetailRoute />} />
            <Route path="/backtests" element={<BacktestListPage />} />
            <Route path="/backtests/:backtestId" element={<BacktestDetailRoute />} />
            <Route path="/walk-forwards" element={<WalkForwardListPage />} />
            <Route path="/walk-forwards/:runId" element={<WalkForwardDetailRoute />} />
            <Route path="/etfs/:etfId" element={<EtfDetailRoute />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </AppShell>
  );
}

function SignalDetailRoute() {
  const signalId = useNumericParam("signalId");
  if (!signalId) {
    return <NotFoundPage />;
  }
  return <SignalDetailPage signalId={signalId} />;
}

function BacktestDetailRoute() {
  const backtestId = useNumericParam("backtestId");
  if (!backtestId) {
    return <NotFoundPage />;
  }
  return <BacktestDetailPage backtestId={backtestId} />;
}

function WalkForwardDetailRoute() {
  const runId = useNumericParam("runId");
  if (!runId) {
    return <NotFoundPage />;
  }
  return <WalkForwardDetailPage runId={runId} />;
}

function EtfDetailRoute() {
  const etfId = useNumericParam("etfId");
  if (!etfId) {
    return <NotFoundPage />;
  }
  return <EtfDetailPage etfId={etfId} />;
}

function useNumericParam(name: string): string | null {
  const value = useParams()[name];
  return value !== undefined && DECIMAL_ID.test(value) ? value : null;
}

function NotFoundPage() {
  return (
    <section className="page not-found-page">
      <div className="page-heading">
        <p>Unknown route</p>
        <h1>Page not found</h1>
      </div>
      <p>The requested page does not exist.</p>
      <Link className="operation-link" to="/">
        Go to Dashboard
      </Link>
    </section>
  );
}

function RouteLoadingFallback() {
  return (
    <div aria-label="Loading page" className="route-loading-fallback" role="status">
      <Skeleton as="block" height="2.5rem" />
      <Skeleton as="block" height="1rem" width="60%" />
      <Skeleton as="block" height="1rem" width="85%" />
    </div>
  );
}

function RouteLoadFailureFallback() {
  return (
    <div className="route-load-failure">
      <p>Unable to load this page.</p>
      <button onClick={() => window.location.reload()} type="button">
        Reload page
      </button>
    </div>
  );
}
