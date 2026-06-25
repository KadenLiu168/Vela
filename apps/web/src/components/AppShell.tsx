import type { ReactNode } from "react";

export type NavItem = {
  href: string;
  label: string;
};

type AppShellProps = {
  activePath: string;
  apiBaseUrl: string;
  children: ReactNode;
  navItems: NavItem[];
  onNavigate: (path: string) => void;
};

export function AppShell({
  activePath,
  apiBaseUrl,
  children,
  navItems,
  onNavigate
}: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Vela Research</h1>
          <span>API: {apiBaseUrl}</span>
        </div>
        <nav aria-label="Research navigation">
          {navItems.map((item) => (
            <a
              aria-current={item.href === activePath ? "page" : undefined}
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
    </div>
  );
}
