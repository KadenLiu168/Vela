## 1. CSS scaffolding (scoped to `apps/web/src/styles.css`)

- [ ] 1.1 Add `.status-pill` base rule using existing tokens: small uppercase text (`var(--text-micro)`), hairline 1px border, 4px radius, padding `var(--spacing-4) var(--spacing-8)`, no shadow
- [ ] 1.2 Add `.status-pill-success` / `.status-pill-partial` / `.status-pill-error` / `.status-pill-neutral` / `.status-pill-loading` variants that map to `--color-pulse-green` / `--color-signal-teal` / `--color-coral-red` / `--color-ash` / `--color-fog` for both border and text; do not introduce new color tokens
- [ ] 1.3 Update `.panel-heading` layout: keep `display: flex; justify-content: space-between; align-items: baseline;`, add a `.panel-heading-status` right slot sized for the pill; ensure the h3 still uses `var(--text-subheading)` and is `min-width: 0` so single-word titles do not push the pill off-screen
- [ ] 1.4 Add `.dashboard-panel .empty-state` override: `background: transparent; border: 1px dashed var(--color-graphite); color: var(--color-fog); padding: var(--spacing-20) var(--spacing-16);` — keep this selector narrow so other `EmptyState` consumers (Signal Detail, Backtest Detail, `market-empty-state`) are unaffected
- [ ] 1.5 Replace `.fetch-log-entry` definition-list styling with a compact block layout: `display: grid; gap: var(--spacing-4) var(--spacing-8); padding: var(--spacing-12) 0; border-top: 1px solid var(--color-graphite);`; first child has no top border
- [ ] 1.6 Add `.fetch-log-entry__head` (row 1: mono timestamp + status pill, `display: flex; justify-content: space-between; align-items: center; gap: var(--spacing-8);`); use `var(--font-jetbrains-mono)` for `.fetch-log-entry__time`
- [ ] 1.7 Add `.fetch-log-entry__meta` (row 2: row counts separated by middle dots, `color: var(--color-mist); font-size: var(--text-caption);`)
- [ ] 1.8 Add `.fetch-log-entry__error` styled as a native `<details>` block: `summary` is `color: var(--color-fog); font-size: var(--text-micro); cursor: pointer;`, the error body uses `var(--font-jetbrains-mono); color: var(--color-mist); font-size: var(--text-caption); overflow-wrap: anywhere; margin-top: var(--spacing-8);`
- [ ] 1.9 Style `.fetch-log-list` scrollbar: add `scrollbar-width: thin; scrollbar-color: var(--color-graphite) transparent;` and a hairline `::-webkit-scrollbar` rule (8px wide, `--color-graphite` thumb, transparent track) so the bounded scroll surface stays visually quiet

## 2. PanelHeading component extension (`apps/web/src/pages/DashboardPage.tsx`)

- [ ] 2.1 Extend `PanelHeading` props with `statusPill?: { label: string; variant: "success" | "partial" | "error" | "neutral" | "loading" }`
- [ ] 2.2 Render the pill in a `.panel-heading-status` slot only when `statusPill` is provided; otherwise leave the right side empty so non-workflow panels (market, strategy, operations) keep their current header

## 3. Signal panel summary (`apps/web/src/pages/DashboardPage.tsx`)

- [ ] 3.1 Update the `signal-panel` `PanelHeading` call to `eyebrow="Latest"` / `title="Signal"`
- [ ] 3.2 Compute `signalStatusPill` from `dashboardState.status` and `signal` props: `loading` while loading, `success` ("Active") when a successful signal is present, `partial` ("Partial") when status is partial, `error` ("Errors") when status is failed, `neutral` ("No data") when `signal` is null
- [ ] 3.3 Pass the computed `signalStatusPill` to `PanelHeading`

## 4. Backtest panel summary (`apps/web/src/pages/DashboardPage.tsx`)

- [ ] 4.1 Update the `backtest-panel` `PanelHeading` call to `eyebrow="Latest"` / `title="Backtest"`
- [ ] 4.2 Compute `backtestStatusPill`: `loading` while loading, `success` ("Active") when a backtest exists with success status, `partial` ("Partial") when backtest status is partial, `error` ("Errors") when backtest status is failed, `neutral` ("No data") when `backtest` is null
- [ ] 4.3 Pass the computed `backtestStatusPill` to `PanelHeading`

## 5. Fetches panel summary (`apps/web/src/pages/DashboardPage.tsx`)

- [ ] 5.1 Update the `fetch-log-panel` `PanelHeading` call to `eyebrow="History"` / `title="Fetches"`
- [ ] 5.2 Compute `fetchStatusPill` from the latest log row: `loading` while loading, `success` ("Active") when latest status is success, `partial` ("Partial") when latest status is partial, `error` ("Errors") when latest status is failed, `neutral` ("No data") when the log list is empty
- [ ] 5.3 Pass the computed `fetchStatusPill` to `PanelHeading`
- [ ] 5.4 Rewrite `FetchLogSummary` so each entry renders a compact 2-row block (`.fetch-log-entry__head` + `.fetch-log-entry__meta`) instead of the 7-row `dl`; remove the per-entry `<dl>` and `Detail` calls for `fetch_time`, `mode`, `status`, `fetched`, `inserted`, `updated`
- [ ] 5.5 For entries with a non-null `error_summary`, render a native `<details>` with `<summary>Show error</summary>` containing the error text; do not render the disclosure when `error_summary` is null

## 6. Test updates (`apps/web/src/App.test.tsx`)

- [ ] 6.1 Update the 12 existing heading lookups (`getByRole("heading", { name: "Latest signal" | "Recent backtest" | "Recent fetches" })`) to the new titles `Signal` / `Backtest` / `Fetches`
- [ ] 6.2 Update related text-content assertions that include the old heading strings (e.g. `Latest signal API unavailable: ...`) to use the new single-word titles so the error-state copy stays in sync
- [ ] 6.3 Add a `data-testid` (e.g. `data-testid="workflow-panel-signal"`, `…-backtest`, `…-fetches`) to each of the three workflow panels so future tests can target panels without depending on the heading string
- [ ] 6.4 Add a unit test for `Signal` panel: with a successful `latest_signal`, the panel header status pill is `success` with label `Active`; with `latest_signal` null, the pill is `neutral` with label `No data`
- [ ] 6.5 Add a unit test for `Backtest` panel: with a populated `recent_backtest`, the pill is `success`; with `recent_backtest` null, the pill is `neutral`
- [ ] 6.6 Add a unit test for `Fetches` panel: with `recent_fetch_logs` empty, the pill is `neutral`; with the latest log having `status: "failed"`, the pill is `error` with label `Errors`
- [ ] 6.7 Add a unit test for the collapsed-error disclosure in `FetchLogSummary`: when an entry has a non-null `error_summary`, the error text is not visible by default; clicking the `<summary>` reveals it

## 7. Validation

- [ ] 7.1 `npm --prefix apps/web run typecheck`
- [ ] 7.2 `npm --prefix apps/web run lint`
- [ ] 7.3 `npm --prefix apps/web run test`
- [ ] 7.4 `npm --prefix apps/web run build`
- [ ] 7.5 `npm --prefix apps/web run dev` and manually inspect the Dashboard at desktop (1280px), 1024px, 900px, and 720px widths: confirm the three workflow panel titles fit on a single line, the status pill is visible top-right of each panel, the empty-state surface is a dashed border (not a darker filled box), and three or more fetch log entries fit inside the 320px scroll boundary without stretching the row
