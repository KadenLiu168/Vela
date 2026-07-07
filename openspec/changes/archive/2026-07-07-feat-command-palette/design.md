## Context

Vela web (`apps/web`) is a React 19 + Vite SPA with three routes (Dashboard, Signal Detail, Backtest Detail) mounted inside an `AppShell` component that owns the global header + nav. The Dashboard page also renders a list of action buttons (Bootstrap / Generate Signal / Run Backtest) and consumes a `DashboardResponse` whose `etf_list` field exposes the ETF catalog the strategy trades. The web client (`apps/web/src/api/client.ts`) already exposes a `listBacktests(limit)` method, a `getLatestStrategySignal()` method, and a `getDashboard()` method that returns the ETF list as part of the aggregate response. No backend search endpoint exists today, and adding one is out of scope for this change (it is captured in the spec's "Deferred follow-ups" scenario).

The web app currently has **no** global keyboard shortcut, no global modal layer, and no client-side data cache. The team's React patterns (per `design-system` and `web-frontend-app` specs) favor: small composable components, error boundaries around route render, the `.app-shell` / `.app-header` / `app-nav` / `app-nav-link` className contract for navigation, and reuse of existing tokens (`--color-paper`, `--surface-slate`, `--radius-cards`, `--shadow-elevated`, `--font-berkeley-mono`) over new ones. The component test stack is Vitest 4 + jsdom + Testing Library; Ladle is used for visual stories.

## Goals / Non-Goals

**Goals:**
- A single, predictable way to jump to any page, recent backtest, or known dashboard action from any focus point in the app, via ⌘K / Ctrl+K (and `/` as a secondary trigger).
- A single inline ETF info affordance so an analyst can confirm "is `VTI` in our universe?" without leaving the palette.
- A component that is testable as a unit (pure filter / sort logic extracted into a helper) and is mockable in Ladle stories without standing up the API.
- Zero new npm dependencies. Zero new tokens. Zero new routes. Zero backend changes.

**Non-Goals:**
- A backend search endpoint that returns cross-entity hits in one response (deferred).
- Fuzzy / typo-tolerant matching — v1 is plain case-insensitive substring.
- A per-ETF detail route — selecting an ETF in v1 only reveals an inline info panel.
- Persistent recent-palette-queries history across reloads.
- User-defined commands or rebindable shortcuts.
- Mobile-first redesign of the AppShell — the palette is desktop-keyboard-first; it must still open on a touch device via a future "search" button (out of scope to add that button now).

## Decisions

### D1 — Where to mount the palette

The palette is mounted **once at the AppShell root**, after `</main>`, via a new `commandPalette?: ReactNode` slot on `AppShell`. `App.tsx` owns the `isPaletteOpen` state and the `useEffect` keydown listener.

- **Why a slot, not a `createPortal` to `document.body`**: keeps the palette's React tree adjacent to the rest of the app, keeps the existing `ErrorBoundary` wrap working without changes, and avoids the SSR/portal-canvas edge cases Vite + Vitest introduce. The overlay is `position: fixed` so it still covers the viewport from inside `</main>`'s sibling position.
- **Why not mount inside `<main>`**: any `overflow: hidden` future style on `main` would clip the overlay; mounting after `</main>` keeps the palette independent of page content overflow rules.

### D2 — Keyboard contract

- **Primary**: `Cmd+K` (macOS) and `Ctrl+K` (everywhere else). Prevented from firing inside `<input>` / `<textarea>` / `[contenteditable]` elements so it doesn't hijack a real text field.
- **Secondary**: `/` opens the palette **only when no input/textarea/contenteditable is focused**. Inside an input `/` types a literal `/`.
- **In-palette shortcuts**:
  - `Escape` closes the palette and restores focus to the element that was focused before opening.
  - `ArrowDown` / `ArrowUp` move the active row within the result list (wraps).
  - `Enter` invokes the active row's `onSelect` handler.
- **Closed palette**: keydown listener is a single no-op, attached to `window` via `useEffect` with the appropriate `addEventListener` / `removeEventListener` cleanup. The listener checks `isPaletteOpen` from a ref to avoid re-binding the handler on every state change.

### D3 — Data sources and freshness

The palette fetches three sources in parallel on each open (via `Promise.all`):
- `listBacktests(10)` — backtest rows.
- `getLatestStrategySignal()` — at most one signal row.
- `getDashboard()` — the `etf_list` field.

All three are already-exposed, tested client methods. The fetch runs **once per open**; results live in `useState` for the lifetime of the open modal and are discarded on close. There is **no shared cache** in v1 (no Zustand / no context) because the palette is the only consumer and re-fetching 3 small endpoints on open is acceptable (and the explicit v1 contract in the spec).

- **Alternatives considered**:
  - *Long-lived client cache* (e.g. SWR / TanStack Query): rejected — adds a new dependency and a new pattern; v1 doesn't need it.
  - *Cache previous-open results in a context provider* so the palette opens instantly with stale data: rejected — adds a new context + a new stale-vs-fresh UX contract that has to be spec'd; v1 ships the simpler "fetch on open" model and the spec captures it as a scenario.

### D4 — Row model and filter algorithm

A typed `CommandPaletteRow` union has four shapes:
- `{ kind: "page"; id: string; label: string; path: string; keywords: string[] }`
- `{ kind: "backtest"; id: string; label: string; path: string; keywords: string[]; runDate: string }`
- `{ kind: "etf"; id: string; label: string; path: null; keywords: string[]; exchange: string; symbol: string; category: string | null }`
- `{ kind: "action"; id: string; label: string; path: null; keywords: string[]; action: () => void | Promise<void> }`

A pure helper `filterCommandRows(query, rows): CommandPaletteRow[]` lives next to the component:
- Empty / whitespace query → return the first **N** rows (N = 20) of the static nav + action groups only. **Backtest and ETF rows are not shown until the user types a query**, to keep the unprompted list short and predictable.
- Non-empty query → case-insensitive substring match against `label` (always) and `keywords` (when present). Match position is recorded (`label` hit > `keyword` hit) for sort priority.
- Sort: `label`-hit rows first, then `keyword`-hit rows, alphabetical within each band, then group-stable (Pages → Backtests → ETFs → Actions, never re-sorted by the filter).
- Result cap: top 50 matches total.

### D5 — Selection behaviors per row kind

- **page** / **backtest** → call `onSelect(path)` (the `navigate` callback the AppShell already receives), then close the palette and restore focus.
- **action** → call `row.action()` inside the same try/catch the Dashboard buttons use today, then close the palette. If the action throws, the `ErrorBoundary` mounted in `App.tsx` catches the failure exactly as it does for the Dashboard action buttons today; the spec says the palette is not responsible for surfacing action errors itself.
- **etf** → set local `expandedEtfId` state, render an inline info panel inside the palette (exchange, symbol, category, name); no navigation. Re-pressing `Enter` on the same ETF toggles the panel closed.

### D6 — Focus management and a11y

- On open: capture `document.activeElement` (via ref) before mounting the dialog; after the dialog mounts, `inputRef.current?.focus()`.
- On close: call the captured element's `.focus()`.
- The dialog is `role="dialog" aria-modal="true" aria-label="Command palette"`. The input is `aria-label="Search"`. The result list is `role="listbox"`; each row is `role="option" aria-selected={row.id === activeRowId}`.
- A focus trap inside the dialog is **not** implemented in v1 (the spec says so explicitly) — `Tab` cycles to the next focusable element on the page. This keeps the v1 small; a follow-up can add a proper focus trap if needed. (Trade-off recorded in Risks.)
- Backdrop click closes the palette.

### D7 — CSS approach

Add a single `.command-palette` block to `apps/web/src/styles.css`. Reuse existing tokens only:
- `--color-paper` for the dialog surface, `--color-ink` for text, `--surface-slate` for the backdrop scrim, `--radius-cards` for the dialog, `--shadow-elevated` for the dialog elevation, `--font-berkeley-mono` for the input.
- No new token declarations in `tokens.css`.

### D8 — Spec scenarios use `data-testid`, not selectors

The spec's WHEN/THEN clauses use `data-testid="command-palette-input"`, `data-testid="command-palette-row"`, `data-testid="command-palette-row-etf-{id}"`, etc. Selector-scoped scenarios are brittle against the design-system rule that descendant-selector buttons / literal class chains must not exist (the team has been bitten by this before — see T2.1 commit body). `data-testid` is the agreed escape hatch.

## Risks / Trade-offs

- **[Risk]** v1 is fetch-on-open with no cache → opening the palette over a slow API feels laggy. → **Mitigation**: the spec records a 100ms perceived-open target (palette shows immediately with the input focused, results populate as data arrives) and a separate "loading" group appears at the top of the result list while any of the three sources is in flight.
- **[Risk]** No focus trap → keyboard-only users can `Tab` out of the palette. → **Mitigation**: the spec explicitly records this trade-off; a follow-up change can add a focus trap. In practice, the only other focusable elements on a Vela page are the nav links and the action buttons, all of which are still keyboard-reachable from outside the palette.
- **[Risk]** `Cmd+K` collides with browser shortcuts on some Linux distros. → **Mitigation**: `event.preventDefault()` only when our handler runs, and we check `e.metaKey || e.ctrlKey`; on macOS this is `Cmd+K`, on Windows/Linux this is `Ctrl+K`. Both are the standard Linear/VSCode/Raycast pattern and are not assigned to any browser default we care about.
- **[Risk]** "Reuse existing tokens only" constrains the visual to whatever tokens are already declared. → **Mitigation**: the design system capability already exposes a sufficient palette for an overlay (surface, ink, radius, shadow, scrim). If a future visual review reveals a gap, it is a follow-up spec change to `design-system`, not a hidden inline override in this change.
- **[Risk]** The `/` shortcut competes with form inputs (Bootstrap form on Dashboard). → **Mitigation**: the keydown handler checks `e.target` against `INPUT|TEXTAREA|SELECT|contenteditable` and only opens the palette when no such element is focused. This is encoded in the spec.

## Migration Plan

- The palette is additive — no existing user-visible flows change. No migration / rollback script is required.
- Rollback: revert the commit. The new component is fully self-contained; the only edits outside `CommandPalette.tsx` are the new `commandPalette` slot on `AppShell` (default-undefined, so removing the prop keeps the prior render byte-identical) and the keydown `useEffect` in `App.tsx`.
- Deploy: ship the commit; no config flags, no environment variables.

## Open Questions

- None for v1. The "true backend search" follow-up is captured in the spec's "Deferred follow-ups" scenario and in the proposal's Out-of-scope list.
