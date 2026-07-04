## 1. Dashboard layout containment (CSS-first, scoped to `apps/web/src/styles.css`)

- [ ] 1.1 Update `.dashboard-grid` so multi-row layouts align panels to the start of each row (`align-items: start`); preserve existing single-column mobile behavior below `720px`
- [ ] 1.2 Bound the `.fetch-log-panel` inner content with a max-height and `overflow-y: auto` (or wrap `.fetch-log-entry` rendering in a scroll container) so long fetch error text cannot expand the panel's row height
- [ ] 1.3 Establish a primary/secondary emphasis split on `.dashboard-panel` elements within `.dashboard-page`: keep primary panels (market, signal, operations) at current visual weight; tighten `.strategy-panel` and `.fetch-log-panel` spacing/typography using existing tokens
- [ ] 1.4 Ensure long paths, timestamps, and failed-symbol error summaries wrap or clip inside their panel without causing horizontal page overflow (use `min-width: 0` + `word-break`/`overflow-wrap` on `.compact-list dd`)

## 2. Operations placement on Dashboard (scoped JSX reordering in `apps/web/src/pages/DashboardPage.tsx`)

- [ ] 2.1 Move the `<article className="dashboard-panel operations-panel">` JSX (currently last in `.dashboard-grid`) to appear directly after the `.signal-panel` and before `.backtest-panel` / `.fetch-log-panel`; preserve all existing roles, labels, buttons, headings, and `data-testid`s
- [ ] 2.2 Verify visual order matches DOM order for keyboard and assistive-technology navigation (no `order:` CSS-only reordering used)

## 3. Empty / loading / error state alignment

- [ ] 3.1 Confirm `.empty-state` blocks on Dashboard's `market-panel`, `signal-panel`, `backtest-panel`, `fetch-log-panel` each name the matching Operations action (market data fetch / generate signal / run backtest) using existing copy, no new copy invention
- [ ] 3.2 Confirm `FeedbackMessage` variants keep `role="status"` for loading/info/success and `role="alert"` for error across all three pages

## 4. Signal Detail & Backtest Detail consistency (`apps/web/src/pages/SignalDetailPage.tsx`, `BacktestDetailPage.tsx`, scoped CSS rules)

- [ ] 4.1 Verify top-level containers reuse `.dashboard-panel` / `.page-heading` / `.empty-state` / `.feedback-message`; fix any divergent utility class while keeping `.holdings-table-wrap` selectors stable
- [ ] 4.2 Verify the Backtest Detail equity-curve block, metric cards, and parameters `<pre>` block keep their existing treatment; ensure the `<pre>` block remains horizontally scrollable inside its panel
- [ ] 4.3 Confirm single-point equity state and empty backtest state remain readable (existing `.empty-state` treatment, no new pattern)

## 5. App Shell API metadata visual weight (`apps/web/src/components/AppShell.tsx` + matching CSS rules)

- [ ] 5.1 Verify the API base URL metadata in `AppShell` does not compete visually with the page heading or primary actions (typography/spacing via existing tokens, no color change)

## 6. Validation

- [ ] 6.1 `npm --prefix apps/web run typecheck`
- [ ] 6.2 `npm --prefix apps/web run lint`
- [ ] 6.3 `npm --prefix apps/web run test`
- [ ] 6.4 `npm --prefix apps/web run build`
- [ ] 6.5 `npm --prefix apps/web run dev` and manually inspect Dashboard in a browser at desktop (1280px), 1024px, 900px, and 720px widths: verify Operations is visible above the fetch-log region on first screen and that long fetch-log content does not stretch sibling panels
