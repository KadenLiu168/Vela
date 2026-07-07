import type { ReactNode } from "react";

export type NavItem = {
  href: string;
  label: string;
};

type AppShellProps = {
  activePath: string;
  apiBaseUrl: string;
  children: ReactNode;
  commandPalette?: ReactNode;
  navItems: NavItem[];
  onNavigate: (path: string) => void;
};

export function AppShell({
  activePath,
  apiBaseUrl,
  children,
  commandPalette,
  navItems,
  onNavigate
}: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-brand">
          <h1>Vela Research</h1>
          <span className="app-api-meta">API: {apiBaseUrl}</span>
        </div>
        <nav aria-label="Research navigation" className="app-nav">
          {navItems.map((item) => (
            <a
              aria-current={item.href === activePath ? "page" : undefined}
              className="app-nav-link"
              href={item.href}
              key={item.href}
              onClick={(event) => {
                event.preventDefault();
                onNavigate(item.href);
              }}
            >
              {item.label}
            </a>
          ))}
        </nav>
      </header>
      <main>{children}</main>
      {commandPalette}
    </div>
  );
}
