## Why

The Dashboard's bottom workflow row (Latest signal, Recent backtest, Recent fetches) currently reads as three unrelated cards rather than one coordinated "data strip". The title `Recent backtest` wraps to two lines in the 1/3-width column while the other two fit on one, breaking the heading rhythm; the empty-state surface uses a darker fill than the panel and reads as a "box inside a box"; each fetch log entry is a 7-row definition list that lets long error text blow past the card boundary and stretch the whole row. With the existing `dashboard-aggregation` data model unchanged, this is a visual-cohesion gap in `apps/web`, not a backend issue.

## What Changes

- Restructure each workflow panel header to `eyebrow + h3 + statusPill`, shortening the h3 to a single word (`Signal` / `Backtest` / `Fetches`) so titles never wrap at desktop, tablet, or mobile widths.
- Add a small status pill in the top-right of each panel derived from the same data the panel renders, using existing color tokens (`--color-pulse-green` / `--color-signal-teal` / `--color-coral-red` / `--color-ash` / `--color-graphite`).
- Restyle the Dashboard's empty-state surfaces to a dashed-border treatment on the panel surface instead of a darker filled box, so the empty state reads as intentional whitespace rather than a nested card.
- Rewrite `FetchLogSummary` so each entry is a compact two-row block (mono timestamp + status pill on row 1, `Fetched / Inserted / Updated` summary on row 2) and long error summaries are collapsed under a native `<details>` toggle.
- Keep the existing `.fetch-log-list` `max-height: 320px; overflow-y: auto` boundary and add a thin styled scrollbar so the bounded area is the only visible scroll surface inside the panel.
- Update `App.test.tsx` heading lookups and any related assertions to match the new single-word titles.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Add a `Dashboard workflow panel visual cohesion` requirement covering the panel header structure (eyebrow + single-word h3 + status pill), the dashed-border empty-state treatment inside Dashboard workflow panels, and the compact two-row fetch log entry with collapsed error summary. Existing `Dashboard focused first-screen hierarchy`, `Dashboard long-content layout resilience`, and `Minimal visual emphasis system` requirements remain in force; this change refines how the Dashboard satisfies them.

## Impact

- `apps/web/src/pages/DashboardPage.tsx` — `PanelHeading` signature extended to accept `statusPill`; `SignalSummary` / `BacktestSummary` / `FetchLogSummary` compute and pass status; `FetchLogSummary` switches from per-entry `dl` to a compact two-row `div` per entry with native `<details>` for errors.
- `apps/web/src/styles.css` — new `.status-pill` and `.panel-heading-status` rules using existing tokens; new `.dashboard-panel .empty-state` override (dashed border, no fill, fog text); compact `.fetch-log-entry` layout; styled thin scrollbar on `.fetch-log-list`.
- `apps/web/src/App.test.tsx` — heading lookups updated from `Latest signal` / `Recent backtest` / `Recent fetches` to `Signal` / `Backtest` / `Fetches`; new tests for status pill derivation and collapsed-error interaction.
- No API, route, data model, shared client contract, dependency, backend behavior, or detail-page change. Mobile single-column behavior below `720px` is preserved unchanged.
