## Why

Vela web has grown to three pages (Dashboard, Signal Detail, Backtest Detail) plus a growing list of dashboard actions (Bootstrap, Generate Signal, Run Backtest) and a catalog of ETFs surfaced by the latest dashboard aggregate. Navigating between them today means either clicking the three nav links in the header or typing a backtest id into the URL bar — both stop scaling once the ETF list and backtest history grow past a handful of entries. A global ⌘K command palette is the cheapest, lowest-risk way to give every page a single jump-to-anything affordance without adding new routes, new state libraries, or new backend endpoints. This change ships the palette as a frontend-only feature that operates on what the web app already knows: the hard-coded nav items, the live `listBacktests` list, the `etf_list` and `latest_signal` returned by `getDashboard`, and the dashboard actions themselves. A true cross-entity backend search is explicitly **out of scope** for this change and is captured as a deferred follow-up.

## What Changes

- Add a new `CommandPalette` component in `apps/web/src/components/CommandPalette.tsx` that renders a modal overlay with a single text input, a scrollable result list grouped by source (Pages, Backtests, ETFs, Actions), and a quiet empty / loading / error state.
- Mount the palette once at the AppShell root via a new `commandPalette` slot, and wire the ⌘K / Ctrl+K / `/` keybindings in `apps/web/src/App.tsx` so any focused element on any route can open it.
- Filter the result list client-side by case-insensitive substring match against the row's `label` and `keywords` (e.g. an ETF row's `keywords` include its `exchange:symbol` form and its `category`).
- Surface the latest backtest list via the existing `listBacktests(10)` API call, the latest signal via `getLatestStrategySignal()`, and the ETF catalog via the `etf_list` field on `getDashboard()`. Data is fetched fresh on each open; results are cached in component state for the lifetime of the open modal (no new state library).
- Expose three dashboard actions in the palette (Bootstrap local database, Generate strategy signal, Run backtest) that delegate to the same code paths the Dashboard buttons call today (the wrappers in `apps/web/src/api/client.ts`). Selecting an action closes the palette and triggers the same `ErrorBoundary`-protected execution the dashboard performs.
- Selecting a Page or Backtest row closes the palette and calls the existing `navigate(path)` callback the AppShell already receives — no router changes.
- Selecting an ETF row does **not** navigate; it expands an inline info panel inside the palette showing exchange, symbol, category, and name. This is explicitly the v1 behavior because no per-ETF route exists yet.
- A new `command-palette` capability spec defines the keyboard contract, the row model, the filter algorithm, the focus / a11y rules, and the out-of-scope backend search.

## Capabilities

### New Capabilities

- `command-palette`: Defines the global ⌘K command palette — keyboard contract, data sources, row model, filter algorithm, selection behaviors per row type, focus management, and the empty / loading / error UX. Out-of-scope (cross-entity backend search) is captured in a "Deferred follow-ups" scenario.

### Modified Capabilities

None. The existing `web-frontend-app` spec gains no new requirements (the palette is rendered by the AppShell, which already has its nav slot pattern; no spec-level contract change is required). The existing `design-system` spec is not touched — the palette uses existing tokens (`--color-paper`, `--surface-slate`, `--radius-cards`, `--shadow-elevated`, `--font-berkeley-mono`) and reuses the `.button-tertiary` class for the close affordance. **No design-system capability change is required for this change.**

## Impact

- New code files:
  - `apps/web/src/components/CommandPalette.tsx`
  - `apps/web/src/components/CommandPalette.test.tsx`
  - `apps/web/src/components/CommandPalette.stories.tsx` (Ladle)
  - `apps/web/src/components/__fixtures__/commandPaletteFixtures.ts` (typed mock data for tests + stories)
- Modified code files:
  - `apps/web/src/components/AppShell.tsx` — accept a `commandPalette?: ReactNode` slot and render it after `</main>` so the modal overlay can cover the viewport without being clipped by `main` overflow.
  - `apps/web/src/App.tsx` — own the `isPaletteOpen` state, the `useEffect` keydown listener (⌘K / Ctrl+K / `/`), and pass the slot.
  - `apps/web/src/components/index.ts` — re-export `CommandPalette` and the `CommandPaletteRow` / `CommandPaletteGroup` types.
- Affected CSS:
  - `apps/web/src/styles.css` — add a `.command-palette` overlay block (backdrop, dialog box, input, row list, group header, info panel) using existing tokens only. No new tokens declared.
  - `apps/web/src/styles/tokens.css` — **not modified** (no new tokens needed).
- New spec file:
  - `openspec/changes/feat-command-palette/specs/command-palette/spec.md`
- Out of scope (deferred follow-ups, documented in the spec):
  - A backend `GET /api/search?q=` endpoint that returns cross-entity hits (signals, backtests, ETFs, holdings) in one response.
  - Fuzzy / typo-tolerant matching (v1 is plain case-insensitive substring).
  - Per-ETF detail route (ETFs only get an inline info panel in v1).
  - Recent-palette-queries persistence across reloads.
  - Customizable user-defined commands / shortcuts.
- No backend changes. No new npm dependencies. No new routes.
