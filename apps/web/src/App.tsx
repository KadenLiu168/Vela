import { useEffect, useState } from "react";
import { getApiBaseUrl } from "./api/client";
import { type NavItem, AppShell } from "./components/AppShell";
import { BacktestDetailPage } from "./pages/BacktestDetailPage";
import { DashboardPage } from "./pages/DashboardPage";
import { SignalDetailPage } from "./pages/SignalDetailPage";

const navItems: NavItem[] = [
  { href: "/", label: "Dashboard" },
  { href: "/signals/demo-signal", label: "Latest Signal" },
  { href: "/backtests/1", label: "Backtest Detail" }
];

export default function App() {
  const [path, setPath] = useState(getCurrentPath);

  useEffect(() => {
    const handlePopState = () => {
      setPath(getCurrentPath());
    };

    window.addEventListener("popstate", handlePopState);

    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  const navigate = (nextPath: string) => {
    if (nextPath !== getCurrentPath()) {
      window.history.pushState({}, "", nextPath);
    }

    setPath(nextPath);
  };

  return (
    <AppShell
      activePath={getActivePath(path)}
      apiBaseUrl={getApiBaseUrl()}
      navItems={navItems}
      onNavigate={navigate}
    >
      {renderRoute(path)}
    </AppShell>
  );
}

function renderRoute(path: string) {
  const signalMatch = path.match(/^\/signals\/([^/]+)$/);

  if (signalMatch) {
    return <SignalDetailPage signalId={decodeURIComponent(signalMatch[1])} />;
  }

  const backtestMatch = path.match(/^\/backtests\/([^/]+)$/);

  if (backtestMatch) {
    return <BacktestDetailPage backtestId={decodeURIComponent(backtestMatch[1])} />;
  }

  return <DashboardPage />;
}

function getActivePath(path: string): string {
  if (path.startsWith("/signals/")) {
    return "/signals/demo-signal";
  }

  if (path.startsWith("/backtests/")) {
    return "/backtests/1";
  }

  return "/";
}

function getCurrentPath(): string {
  return window.location.pathname;
}
