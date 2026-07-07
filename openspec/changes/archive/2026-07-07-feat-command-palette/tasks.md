## 1. Test fixtures and pure filter helper

- [x] 1.1 Add `apps/web/src/components/__fixtures__/commandPaletteFixtures.ts` with typed `makePageRow`, `makeBacktestRow`, `makeEtfRow`, `makeActionRow` factories and a `sampleCommandPaletteRows` array covering all four row kinds.
- [x] 1.2 Add `apps/web/src/components/commandPaletteFilter.ts` exporting `filterCommandRows(query, rows): CommandPaletteRow[]` and the `CommandPaletteRow` discriminated union (page / backtest / etf / action). Implement the spec's algorithm: empty query returns pages + actions only, capped at 20; non-empty query is case-insensitive substring on `label` + `keywords`, `label`-hit rows first, alphabetical within band, group-stable order, capped at 50.

## 2. CommandPalette component

- [x] 2.1 Add `apps/web/src/components/CommandPalette.tsx` with props `{ isOpen: boolean; onClose: () => void; pages: PageRow[]; onNavigate: (path: string) => void; fetchBacktests: () => Promise<BacktestListResponse>; fetchLatestSignal: () => Promise<LatestStrategySignalResponse>; fetchDashboard: () => Promise<DashboardResponse>; actions: ActionRow[] }`. Internal state: `query`, `activeRowId`, `expandedEtfId`, `loadingSources: Set<"backtests" | "signals" | "dashboard">`, `errorSources: Set<...>`, `backtests`, `latestSignal`, `dashboard`.
- [x] 2.2 In `useEffect([isOpen])`, when `isOpen` flips to `true`: (a) call `document.activeElement` capture, (b) call `inputRef.current?.focus()`, (c) kick off the three `Promise.allSettled` fetches and update state.
- [x] 2.3 Implement the `useEffect` keydown listener on `window`: handle `Cmd+K` / `Ctrl+K` (toggle, preventDefault when handled), `/` (open only when focus is not in `input/textarea/select/contenteditable`), `Escape` (close), `ArrowDown` / `ArrowUp` (move active row, wrap), `Enter` (invoke active row). Attach/detach with the standard cleanup. Use a ref to read latest `isOpen` without re-binding the listener.
- [x] 2.4 Render the dialog: backdrop (`data-testid="command-palette-backdrop"`), dialog box (`data-testid="command-palette"`), input (`data-testid="command-palette-input"`), loading group (`data-testid="command-palette-loading"`), error rows (`data-testid="command-palette-error"`), grouped result list (`role="listbox"`), per-row `data-testid="command-palette-row"` and `data-testid="command-palette-row-active"`, ETF info panel (`data-testid="command-palette-etf-info-{id}"`), empty state (`data-testid="command-palette-empty"`).
- [x] 2.5 Wire the per-row click + keyboard `Enter` to a single `activateRow(row)` function that branches on `row.kind` per the spec's "Selection behavior per row kind" requirement.
- [x] 2.6 Re-export the component and types from `apps/web/src/components/index.ts`.

## 3. AppShell slot and App.tsx wiring

- [x] 3.1 Extend `AppShellProps` with `commandPalette?: ReactNode` and render `{commandPalette}` after `</main>` inside `.app-shell`.
- [x] 3.2 In `App.tsx`, add `isPaletteOpen` state and the keydown `useEffect` (global `Cmd+K` / `Ctrl+K` / `/` that flips the state). Pass a `<CommandPalette ...>` instance to `<AppShell commandPalette={...}>`. The keydown listener inside the component is the source of truth; the App-level one is a no-op once the component owns the keydown. (Implementation note: keep the App-level keydown handler that opens the palette, and let the component's keydown handler own `Escape` / arrows / `Enter` / toggle-when-already-open.)
- [x] 3.3 Define the three `ActionRow` instances: `{ id: "action-bootstrap", label: "Bootstrap local database", action: () => bootstrapLocalDatabase() }`, `{ id: "action-generate-signal", label: "Generate strategy signal", action: () => generateStrategySignal() }`, `{ id: "action-run-backtest", label: "Run backtest", action: () => runBacktest(...) }` (passing the same date arguments the Dashboard button uses today — `useState` for start/end date is already on the Dashboard; pass them down via a small store or by lifting the form state into `App.tsx`). For v1, accept the simpler refactor: lift the start/end date `useState` into `App.tsx` and pass `startDate`, `endDate` to both the Dashboard form and the palette.

## 4. CSS

- [x] 4.1 Append a `.command-palette` block to `apps/web/src/styles.css` with rules for `.command-palette-backdrop`, `.command-palette-dialog`, `.command-palette-input`, `.command-palette-groups`, `.command-palette-group-header`, `.command-palette-row`, `.command-palette-row-active`, `.command-palette-etf-info`, `.command-palette-empty`, `.command-palette-error`, `.command-palette-loading`. All values SHALL reference existing tokens from `apps/web/src/styles/tokens.css` only.
- [x] 4.2 Verify `apps/web/src/styles/tokens.css` is unchanged (byte-identical to pre-change `git show HEAD:apps/web/src/styles/tokens.css`).

## 5. Tests

- [x] 5.1 Add `apps/web/src/components/CommandPalette.test.tsx` covering: filter helper (empty query returns pages+actions only, cap 20; non-empty query matches label+keywords, label-hit first, group-stable order, cap 50; no matches returns empty list), keyboard contract (Cmd+K opens, `/` opens from non-input, `/` inside input types literal `/`, Escape closes, ArrowDown wraps, Enter activates), data fetching (3 sources fetched in parallel on open, API failure renders quiet error row), selection behavior (page navigates and closes, backtest navigates and closes, action invokes the action and closes, ETF expands info panel without navigating, Enter on expanded ETF closes the panel), backdrop click closes, focus restoration on close.
- [x] 5.2 Confirm `apps/web/src/App.test.tsx` still passes (no regressions from the new `commandPalette` slot — default-undefined must keep the prior render).

## 6. Ladle stories

- [x] 6.1 Add `apps/web/src/components/CommandPalette.stories.tsx` with stories: `Closed`, `OpenWithNoQuery`, `OpenWithBacktestsLoaded`, `OpenWithEtfsLoaded`, `OpenWithError`, `OpenWithSelectedEtfInfo`. Stories SHALL use the fixtures from `commandPaletteFixtures.ts` and SHALL NOT hit the network.

## 7. Validate

- [x] 7.1 `cd apps/web && npm run typecheck && npm run lint && npm run lint:css && npm run test`. All pass.
- [x] 7.2 `cd /Users/kaden/Vela && openspec validate feat-command-palette`. Passes.
- [x] 7.3 `npx --prefix apps/web ladle build`. Succeeds (story bundle compiles).
- [x] 7.4 `cd /Users/kaden/Vela && uv run pytest -q --ignore=packages/core/tests/test_dashboard_aggregation.py`. Still 413 passed (no Python regressions).
