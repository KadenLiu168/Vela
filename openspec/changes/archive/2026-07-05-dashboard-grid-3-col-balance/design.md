## Context

The dashboard at `apps/web/src/pages/DashboardPage.tsx` renders six `<article class="dashboard-panel …">` children inside one `.dashboard-grid` container:

- Row 1: `.market-panel` + `.strategy-panel` (2 panels)
- Row 2: `.operations-panel` (1 panel, full width)
- Row 3: `.signal-panel` + `.backtest-panel` + `.fetch-log-panel` (3 panels)

The current desktop grid in `apps/web/src/styles.css` is `repeat(4, minmax(0, 1fr))`. Row 1 is balanced via `span 2` on each panel, Row 2 is balanced via `span 4` on Operations, but Row 3 has only 3 panels and no `span` declarations, so the 4th column slot stays empty and produces the visible whitespace to the right of the Fetches panel.

Existing responsive breakpoints already cover narrower viewports:
- `@media (max-width: 1024px)` switches to `repeat(2, …)` and gives Market/Strategy/Operations `span 2`.
- `@media (max-width: 720px)` switches to `1fr` (single column).

This change targets the **default desktop layout** (viewport > 1024px) only. The tablet and mobile breakpoints stay as-is to keep this change minimal.

## Goals / Non-Goals

**Goals:**
- Eliminate the trailing-column whitespace in the desktop dashboard bottom row.
- Keep the grid balanced across all three rows (each row sums to the column count).
- Keep the change CSS-only: no JSX, no new components, no new tokens.
- Preserve existing responsive behavior at 1024px and 720px breakpoints.

**Non-Goals:**
- Restructuring the panel content (no copy or layout changes inside any panel).
- Adding a new panel or filling the freed space with new information.
- Touching `.workflow-grid` (used on Signal/Backtest detail pages) — out of scope.
- Adjusting tablet (≤1024px) or mobile (≤720px) layouts in this change.
- Introducing new design tokens, theme variables, or typography changes.

## Decisions

### Decision 1: Switch desktop grid from 4 to 3 columns

Change `.dashboard-grid` from `repeat(4, minmax(0, 1fr))` to `repeat(3, minmax(0, 1fr))`.

**Rationale:** With 3 panels in the bottom row, 3 columns is the natural fit. 4 columns was the cause of the whitespace, and 2 columns would compress the top row too tightly (Market + Strategy have meaningful detail content).

**Alternatives considered:**
- *Add a 4th panel to fill the trailing slot.* Rejected: out of scope, requires a new data source or component, and a forced content addition is worse than an empty grid slot.
- *Make `.fetch-log-panel` `span 2` and keep 4 columns.* Rejected: the Fetches panel is a list with a small fixed number of rows; widening it does not improve information density, and the top row would still feel over-stretched.

### Decision 2: Redistribute top-row spans as `market-panel: span 1` and `strategy-panel: span 2`

In a 3-column grid, `span 2 + span 2` no longer fits. Distribute as 1 + 2.

**Rationale:** `.strategy-panel` renders 7 `<dt>/<dd>` rows (Version, Momentum windows, Score weights, Top N, Defensive asset, Trading cost, Universe); it benefits from a wider slot. `.market-panel` renders 2 metrics and 2 date rows; it reads well in a single column at desktop width.

**Alternatives considered:**
- *Market `span 2`, Strategy `span 1`.* Rejected: visually inverts the content density (Strategy is the denser panel).
- *Stack Market and Strategy as a single column each on the same row at 1 + 1, leaving the 3rd column for a new panel.* Rejected: introduces scope creep (new panel).

### Decision 3: Update `.operations-panel` `span 4` → `span 3`

`grid-column: span 4` no longer matches the 3-column grid track count. `span 3` preserves "full row width" semantics.

### Decision 4: Leave `.signal-panel`, `.backtest-panel`, `.fetch-log-panel` unspanned

Each naturally occupies 1 of the 3 equal columns, filling the bottom row with no whitespace.

### Decision 5: CSS-only change, no JSX edits

`DashboardPage.tsx` already has the correct panel order and correct class names. Adjusting the `grid-column` rules in CSS is the minimum-surface-area fix.

## Risks / Trade-offs

- **Strategy panel content overflow at narrow desktop widths (≈1024–1280px).** The Strategy detail list has long values such as `SSE:511010` and `config/etf_pool.yaml`; in a 2/3-width column they may wrap or feel cramped. → **Mitigation:** `.compact-list` already uses `min-width: 0` on the parent grid and standard `dl/dt/dd` flow; verify visually at 1280px and 1366px after the change. If wrapping is unacceptable, add a `text-overflow: ellipsis` rule scoped to the value `<dd>`.
- **Inconsistent tablet/mobile layouts still have a similar whitespace problem at the 720–1024px range** (2 columns with an odd number of bottom-row panels). → **Mitigation:** explicitly out of scope for this change; flag as a follow-up if the user wants the same fix applied to the 1024px breakpoint.
- **CSS-only change cannot be unit-tested.** → **Mitigation:** rely on the existing Vite dev server (`npm --prefix apps/web run dev`) and visual verification at common desktop widths (1280px, 1366px, 1440px, 1920px). The frontend skeleton test suite (`apps/web/src/App.test.tsx`) does not cover layout, so no test changes are required.
- **Reduced-motion and color tokens are unchanged**, so accessibility properties (focus rings, contrast, animation durations) are preserved by construction.

## Open Questions

None. All decisions are decided in this design.
