## Why

The web application manually synchronizes browser history, path state, regular-expression matching, and page dispatch in `App.tsx`. Ten production detail links bypass that mechanism through native anchors, causing full page reloads and losing intentionally lifted Dashboard backtest-form state; unmatched paths also silently render Dashboard rather than an explicit 404.

Routing is now a cross-cutting correctness boundary for every existing page and navigation entry. Replacing the bespoke implementation with a declarative Router makes navigation behavior, route ownership, parameters, and unknown-path handling explicit before additional pages make the current approach more fragile.

## What Changes

- Add a browser-history React Router dependency and declare the existing Dashboard, Signals, Backtests, Walk-forward, and ETF routes in one route tree.
- Replace bespoke `pushState`/`popstate`/regular-expression route dispatch, Walk-forward completion redirects, and Signal source-query updates with Router navigation, route parameters, search-parameter APIs, and a catch-all not-found page.
- Replace every production internal page anchor with Router links; use Router programmatic navigation for AppShell-adjacent command-palette selection and completion redirects.
- Preserve the Dashboard backtest form state across in-app route transitions, retain existing lazy route loading and route-failure recovery, and reject non-numeric detail parameters without calling a detail API.
- Keep all public frontend paths, API contracts, data fetching behavior, Dashboard content, database behavior, and local-only deployment scope unchanged.

## Capabilities

### New Capabilities

- `web-client-routing`: Defines declarative browser routing, internal navigation without document reloads, valid detail parameters, unknown-path handling, and route-transition state preservation for the web application.

### Modified Capabilities

- None.

## Impact

- Affected frontend runtime: `apps/web/package.json`, `apps/web/package-lock.json`, `apps/web/src/App.tsx`, `apps/web/src/components/AppShell.tsx`, `apps/web/src/components/CommandPalette.tsx`, `apps/web/src/pages/SignalListPage.tsx`, `apps/web/src/pages/WalkForwardListPage.tsx`, and the existing page components that render internal detail links.
- Affected tests: application-route, command-palette, and page-component tests will exercise Router context, internal navigation, invalid parameters, and the not-found page.
- Existing `web-route-code-splitting` requirements remain mandatory: non-default pages stay lazy, AppShell remains persistent during loading/failure, and the established bundle check must be evaluated from a clean build. This Change does not authorize unmeasured budget relaxation.
- No API, backend, SQLite schema, migration, persistent database, or deployment-host configuration changes.
