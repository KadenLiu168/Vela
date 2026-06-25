import type { ReactNode } from "react";

type AppShellProps = {
  apiBaseUrl: string;
  children: ReactNode;
};

export function AppShell({ apiBaseUrl, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Vela Web</h1>
        <span>API: {apiBaseUrl}</span>
      </header>
      <main>{children}</main>
    </div>
  );
}
