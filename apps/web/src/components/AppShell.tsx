import { useRef, type ReactNode } from "react";
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
  const mainRef = useRef<HTMLElement>(null);

  return (
    <div className="app-shell">
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          // Focus the region directly: the fragment target is focusable, but
          // moving focus here is what makes the skip link work in every
          // browser rather than only where fragment focus is implemented.
          event.preventDefault();
          mainRef.current?.focus();
        }}
      >
        Skip to main content
      </a>
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
      <main id="main-content" ref={mainRef} tabIndex={-1}>
        {children}
      </main>
      {commandPalette}
    </div>
  );
}
