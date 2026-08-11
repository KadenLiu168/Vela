## Context

`App.tsx` currently owns browser-history mutation, a `popstate` listener, pathname state, regular-expression parameter extraction, active-navigation derivation, and fallback page selection. Production detail links render as native anchors, so they bypass the App-owned path state and reload the document. `WalkForwardListPage` separately pushes history and dispatches a synthetic `popstate` after a completed run, while `SignalListPage` reads and rewrites `window.location` for its `source` query parameter.

The existing public paths are `/`, `/signals`, `/signals/:signalId`, `/backtests`, `/backtests/:backtestId`, `/walk-forwards`, `/walk-forwards/:runId`, and `/etfs/:etfId`. Dashboard's backtest dates are intentionally owned above the currently rendered page. Non-default pages already use `lazy`, `Suspense`, and a route-keyed error boundary; those contracts, existing API requests, and detail-level API 404 states must remain intact.

The project is local-only and Vite serves the application during development. The existing bundle checker evaluates a previously built `dist/` tree and currently reports an over-budget initial graph before this Change, so implementation must build before treating bundle output as evidence. This Change must not loosen the established `web-route-code-splitting` budgets without a separate evidence-backed specification change.

## Goals / Non-Goals

**Goals:**

- Make one browser-history Router authoritative for all existing web paths, route parameters, search updates, and programmatic redirects.
- Make all production internal page navigation stay in the mounted application, preserving Dashboard's lifted backtest dates during in-app transitions.
- Render an explicit, accessible not-found page for unmatched paths and malformed detail identifiers without sending detail API requests.
- Retain lazy route modules, persistent AppShell, loading/failure recovery, current public URLs, API request semantics, keyboard behavior, and visual styling.

**Non-Goals:**

- Changing public URL shapes, adding an ETF list page, introducing route loaders/actions, or moving existing page data fetching into Router APIs.
- Persisting Dashboard form values across a document refresh, browser restart, or a new tab.
- Changing backend APIs, database schemas, migrations, local SQLite data, or deployment hosting configuration.
- Relaxing bundle budgets or broadly refactoring unrelated page/state code.

## Decisions

### 1. Use declarative `BrowserRouter` routes, not a data router or another hand-written history adapter

Add `react-router-dom` with the npm lockfile recording its exact resolved version. The application root will compose a `BrowserRouter` around an App content component that can use Router hooks; the route content will remain inside `AppShell`, the existing `ErrorBoundary`, and the existing `Suspense` boundary.

`Routes` will declare the eight existing path forms and a final `*` route. Browser history, direct in-app navigation, and Back/Forward behavior are then owned by Router instead of local pathname state and synthetic events.

`createBrowserRouter` with loaders/actions was considered but rejected: every page already owns carefully tested request/loading/error state, so moving data ownership is unnecessary scope. Continuing the custom router was rejected because it cannot make native page links, page-level redirects, and route fallbacks share one authority.

### 2. Keep Dashboard state above `Routes`; use Router primitives at every navigation boundary

The lifted Dashboard backtest form remains in the App content component above `Routes`. `AppShell` will render `NavLink` entries so Router supplies active-page semantics. Every production link to a Vela page will render `Link`; code paths that navigate after a command-palette selection or an accepted Walk-forward run will call `useNavigate()`.

`SignalListPage` will derive and update its `source` filter from Router location/search state rather than `window.location` and `history.replaceState`. Its replacement navigation must reconstruct the current pathname, preserved unrelated query parameters, and hash so the existing filter URL contract remains unchanged.

Native anchors remain appropriate only for external resources; the route-load failure's explicit `window.location.reload()` remains a recovery action, not application navigation.

### 3. Guard dynamic identifiers before rendering a detail page

React Router parameters match arbitrary path segments, while the current regular expressions accept only one or more digits. Small route-adapter components will read `useParams()`, accept only the existing decimal-digit form, and pass the validated string to the existing detail page. Missing or invalid identifiers render the shared not-found page and issue no detail API request.

This preserves existing parameter acceptance rather than silently broadening `/signals/:signalId`, `/backtests/:backtestId`, `/walk-forwards/:runId`, or `/etfs/:etfId` to arbitrary text. API 404s for syntactically valid but unknown ids remain the responsibility of the existing detail pages.

### 4. Retain lazy boundaries and error-reset behavior

The existing lazy page imports remain module-level and route elements render them below the existing `Suspense` fallback. `useLocation().pathname` replaces local pathname state as the error-boundary reset key, so navigating away from a failed chunk still restores rendering without removing AppShell.

The Router package is part of the initial static graph because the root needs it before it can choose a route. Its measured build effect must be reviewed with the existing bundle checker after a clean build; no vendor-chunk or budget change is implied by this design.

## Risks / Trade-offs

- [A BrowserRouter needs an SPA fallback when later hosted] → Vite covers local development and production deployment is out of scope; any future static host must serve `index.html` for client paths before it is supported.
- [A dynamic Router parameter would otherwise accept non-numeric identifiers] → Validate route parameters before detail components mount and cover every malformed identifier with no-request tests.
- [A missed internal anchor or direct history mutation would retain a reload/state-loss path] → Audit production TSX for internal `href`, `window.history`, and `window.location`; preserve only the explicit chunk-recovery reload.
- [Router context can invalidate isolated component tests] → Wrap affected application/page tests in an appropriate Router and replace assertions tied to synthetic `popstate` with observable route behavior.
- [Route refactoring could regress code splitting or exceed an existing size budget] → Run a clean build followed by the established bundle checker; treat a budget failure as evidence for a separate scoped decision, not permission to weaken the check.

## Migration Plan

1. Add the Router dependency and lockfile entry, then introduce the root provider and declarative route map while retaining current route modules and page props.
2. Convert navigation boundaries and URL-query ownership, add the not-found and numeric-parameter guards, and remove only the superseded manual-history code.
3. Update focused Router-context tests, then run the complete frontend gate and browser acceptance at the required desktop and narrow viewports.
4. If a regression is found, revert the scoped frontend dependency/source/test changes together; no data migration or persistent-state rollback is required.

## Open Questions

None. The locked Router version will be selected through npm at implementation time and must be compatible with the repository's React 19 dependency.
