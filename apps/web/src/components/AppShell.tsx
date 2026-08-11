import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

export type NavItem = {
  href: string;
  label: string;
};

type AppShellProps = {
  apiBaseUrl: string;
  children: ReactNode;
  commandPalette?: ReactNode;
  navItems: NavItem[];
};

export function AppShell({ apiBaseUrl, children, commandPalette, navItems }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-brand">
          <p className="app-brand-title">Vela Research</p>
          <span className="app-api-meta">API: {apiBaseUrl}</span>
        </div>
        <nav aria-label="Research navigation" className="app-nav">
          {navItems.map((item) => (
            <NavLink
              className="app-nav-link"
              key={item.href}
              to={item.href}
              end={item.href === "/"}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main>{children}</main>
      {commandPalette}
    </div>
  );
}
