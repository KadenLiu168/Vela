## Why

Two unrelated drift items prevent the `design-system` capability from
being the single source of truth for the web frontend:

1. **F-204 (line-height magic values)**: `apps/web/src/styles.css`
   declares `line-height: 1.15` at four call sites (lines 443, 480,
   537, 747). The `design-system` capability requires every
   typography property to come from a `--leading-*` token; this is a
   zero-decision cleanup.
2. **F-206 (page-level h1 / Trunk Test)**: the `Web.trunk-test` a11y
   contract requires every page in the `<main>` landmark to begin
   with exactly one `<h1>`. Today each page (Dashboard, Signal
   Detail, Backtest Detail) starts with a `<h2>`, while the brand
   `<h1>Vela Research</h1>` lives in the AppShell banner landmark.
   Two `h1`s in different landmarks is technically valid, but the
   page-content heading carries the page identity and is currently a
   non-h1.

Both are mechanical, low-risk changes that have been parked behind
the Initiative's design-system promotion. They should land together
because neither alone ships a user-visible improvement and both close
open spec compliance findings.

## What Changes

- **Add `--leading-tight: 1.15;`** to `apps/web/src/styles/tokens.css`
  (alongside the existing `--leading-*` scale).
- **Replace** the four `line-height: 1.15;` declarations in
  `apps/web/src/styles.css` with `line-height: var(--leading-tight);`.
- **Change** the page-level heading in each of the three pages
  from `<h2>` to `<h1>`:
  - `apps/web/src/pages/DashboardPage.tsx` — "Workflow Dashboard"
  - `apps/web/src/pages/SignalDetailPage.tsx` — "Signal Detail"
  - `apps/web/src/pages/BacktestDetailPage.tsx` — "Backtest Detail"
- **Verify** that exactly one `<h1>` lives inside each page's
  rendered tree (AppShell's brand h1 remains in the banner landmark,
  page h1 remains in the main landmark; different landmarks → OK).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `design-system`: Adds a line-height-token coverage requirement and
  a page-level heading requirement (one scenario each).
- `web-frontend-app`: Adds a page-level h1 requirement (one
  scenario).

## Impact

- Affected code:
  - `apps/web/src/styles/tokens.css` (1 new token, 1 line)
  - `apps/web/src/styles.css` (4 line replacements)
  - `apps/web/src/pages/DashboardPage.tsx` (1 line)
  - `apps/web/src/pages/SignalDetailPage.tsx` (1 line)
  - `apps/web/src/pages/BacktestDetailPage.tsx` (1 line)
- Affected specs:
  - delta to `openspec/specs/design-system/spec.md`
  - delta to `openspec/specs/web-frontend-app/spec.md`
- Validation: existing frontend lint, typecheck, test, build; plus
  `openspec validate add-design-system-cleanup-fixes`; plus a manual
  visual QA pass confirming the page heading hierarchy in DevTools
  (Elements → Accessibility tree shows one `<h1>` per page in
  `<main>`).
- No API, no backend, no test fixture changes.

## Out of scope

- No additional heading-level changes elsewhere (the `<h3>` cascade
  inside `holdings-section` etc. is already a separate matter in
  Initiative F-305's later phases).
- No introduction of `--leading-tight-2: 1.12` or other fine-grained
  variants; one step covers all four sites.
