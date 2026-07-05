## 1. Update dashboard grid CSS

- [x] 1.1 In `apps/web/src/styles.css`, change the `.dashboard-grid` rule's `grid-template-columns` from `repeat(4, minmax(0, 1fr))` to `repeat(3, minmax(0, 1fr))`
- [x] 1.2 In the same rule block, keep `gap`, `padding`, and other properties unchanged
- [x] 1.3 In the panel-span rules, change `.market-panel` from `grid-column: span 2` to `grid-column: span 1`
- [x] 1.4 In the panel-span rules, keep `.strategy-panel` at `grid-column: span 2`
- [x] 1.5 In the panel-span rules, change `.operations-panel` from `grid-column: span 4` to `grid-column: span 3`
- [x] 1.6 Confirm `.signal-panel`, `.backtest-panel`, and `.fetch-log-panel` have no `grid-column` declarations (they occupy 1 column each by default)

## 2. Verify behavior

- [x] 2.1 Run `npm --prefix apps/web run typecheck` and `npm --prefix apps/web run build` to confirm no regressions
- [x] 2.2 Start the dev server (`npm --prefix apps/web run dev`) and open `/` at a desktop viewport (≥ 1280px wide); confirm the three bottom-row panels (Signal, Backtest, Fetches) each fill one column with no trailing whitespace, the Operations panel still spans the full row, and the top row shows Market (1/3 width) and Strategy (2/3 width)
- [x] 2.3 Resize to ≤ 1024px and ≤ 720px; confirm the existing responsive breakpoints still produce 2-column and 1-column layouts respectively, with no layout breakage
- [x] 2.4 Visually scan the Strategy panel at 1280px and 1366px to confirm the detail list (Version, Momentum windows, Score weights, Top N, Defensive asset, Trading cost, Universe) does not overflow or wrap awkwardly; if it does, add a scoped `text-overflow: ellipsis` on the value `<dd>` and re-verify
