## 1. Token

- [x] 1.1 Add `--leading-tight: 1.15;` to
      `apps/web/src/styles/tokens.css` in the typography scale
      group, alphabetically positioned next to
      `--leading-subheading`

## 2. Replace magic values

- [x] 2.1 In `apps/web/src/styles.css`, replace the four
      `line-height: 1.15;` declarations (currently at lines
      443, 480, 537, 747) with
      `line-height: var(--leading-tight);`
- [x] 2.2 Verify no `line-height: 1.15` remains in
      `apps/web/src/styles.css` (use
      `grep -n "line-height: 1.15" apps/web/src/styles.css`)
- [x] 2.3 Update five `h2` CSS selectors in `apps/web/src/styles.css`
      that targeted the page-identity heading to `h1` instead,
      to keep the visual treatment consistent with the
      `<h2>` → `<h1>` rename in tasks 3.1–3.3:
      - `.page-heading h2` (lines 172 and the responsive
        override at line 1336)
      - `.dashboard-heading h2` (lines 194 and the responsive
        overrides at lines 1239 and 1362)
      This was an apply-time cascade finding, not a separate
      change; tasks 3.1–3.3 without this would have left the
      page title rendering at body default 15px mist on
      every page.

## 3. Page headings

- [x] 3.1 In `apps/web/src/pages/DashboardPage.tsx`, change
      the `<h2>Workflow Dashboard</h2>` element to `<h1>`
- [x] 3.2 In `apps/web/src/pages/SignalDetailPage.tsx`, change
      `<h2>Signal Detail</h2>` (or whichever h2 sits at the
      page-identity position) to `<h1>`
- [x] 3.3 In `apps/web/src/pages/BacktestDetailPage.tsx`, change
      the page-identity `<h2>` to `<h1>`

## 4. Validation

- [x] 4.1 `openspec validate add-design-system-cleanup-fixes`
      passes
- [x] 4.2 `npm --prefix apps/web run typecheck` passes
- [x] 4.3 `npm --prefix apps/web run lint` passes
- [x] 4.4 `npm --prefix apps/web run test` passes
- [x] 4.5 `npm --prefix apps/web run build` passes
- [x] 4.6 `uv run pytest -q` (full project) passes
- [x] 4.7 DevTools a11y tree spot-check on each of the three
      pages confirms exactly one `<h1>` inside `<main>` and
      the brand `<h1>Vela Research</h1>` in `<header>`
- [x] 4.8 `openspec-archive-change add-design-system-cleanup-fixes`
      archives the change

