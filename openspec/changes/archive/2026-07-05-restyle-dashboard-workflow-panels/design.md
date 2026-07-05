## Context

`apps/web` is a Vite + React + TypeScript SPA using the Linear-style design system documented in `DESIGN.md` (midnight precision: `--color-void` canvas, paper-white type, single acid-lime action accent, hairline borders, compact 8–12px paddings, 6/12px radii). Design tokens live in `variables.css` and are wired into `apps/web/src/styles.css`; both files are part of the same change set.

The Dashboard's bottom workflow row lives inside the `.workflow-grid` (3 equal columns at desktop, 1 column below `720px`) and currently renders three panels — `signal-panel`, `backtest-panel`, `fetch-log-panel`. Each panel is a `.dashboard-panel` with a `.panel-heading` (eyebrow + h3) and a summary body. The current implementation has three visible cohesion problems that this design resolves.

1. The h3 sizes use `--text-subheading` (24px); within a 1/3-width column the text "Recent backtest" wraps to two lines while "Latest signal" and "Recent fetches" stay on one, breaking the visual rhythm of the row.
2. The shared `EmptyState` component renders a `var(--surface-carbon)` filled box — darker than the panel's `var(--surface-obsidian)` — which reads as a "card inside a card" when the panel itself is empty.
3. `FetchLogSummary` renders each log entry as a full 7-row `dl`; combined with long untruncated `error_summary` strings, the entries push the panel past its 320px scroll boundary, expanding the row and the page.

Existing requirements in `openspec/specs/web-frontend-app/spec.md` already require bounded fetch history (`Dashboard long-content layout resilience`) and ordered status/operations on the first screen (`Dashboard focused first-screen hierarchy`). This change refines how the Dashboard satisfies them, by adding a `Dashboard workflow panel visual cohesion` requirement that codifies the header structure, empty-state treatment, and fetch log entry shape.

## Goals / Non-Goals

**Goals:**

- Make the three workflow panels read as a coordinated data strip: same header pattern, same status encoding, same body density rhythm.
- Encode per-panel status at a glance via a small pill in the top-right of each panel, reusing the existing tokenized status palette.
- Bound the Recent fetches content inside the panel using a compact 2-row entry shape plus a native collapsed-error disclosure, so the existing `max-height: 320px; overflow-y: auto` boundary always contains the visible content.
- Eliminate the "box inside a box" empty state on the Dashboard by switching the in-panel empty state to a dashed-border treatment on the panel surface.
- Keep all changes scoped to the Dashboard's `.workflow-grid` row; do not touch `.dashboard-grid` (market/strategy/operations), the detail pages, or shared `EmptyState` consumers elsewhere.

**Non-Goals:**

- No new design tokens, themes, or color systems — only existing `variables.css` tokens and the small additions in the new CSS block.
- No API, route, data model, or shared client contract changes.
- No detail-page refactor (Signal/Backtest detail panels keep their current treatment).
- No new layout grid (3 equal columns stays; mobile 1-column behavior below `720px` is preserved).
- No new third-party dependency (native `<details>` for the error collapse).
- No renaming of the section eyebrow strings (only the h3 shortens).

## Decisions

### Decision 1: Title compression at the h3 layer, not the eyebrow layer

The eyebrow is `LATEST` (signal), `LATEST` (backtest), `HISTORY` (fetches) — short, uppercase, 13px, fog color. The h3 currently uses the 24px `--text-subheading` token, which is what forces "Recent backtest" to wrap. Two alternatives were considered:

- **Reduce h3 to 18–20px.** Keeps the descriptive title but adds a new in-between size that would also need to land in `variables.css` and propagate.
- **Shorten h3 to a single word and let the eyebrow carry context.** `Signal` / `Backtest` / `Fetches` paired with `LATEST` / `LATEST` / `HISTORY` is unambiguous, fits the 1/3 column at all desktop widths, and matches the Linear-style tendency to be terse.

We pick the second — it requires no new typography token and produces a tighter visual rhythm. The h3 keeps `--text-subheading` (no new token); only the strings change.

### Decision 2: Status pill in the panel header, no top accent rail

Two encodings were considered for the at-a-glance status:

- **Thin top accent rail (2–3px) on each card in the status color.** Strong visual unity, but adds a second visual layer on top of the existing border, and the Linear design system uses hairline borders — a thicker rail would compete with that.
- **Status pill in the top-right of the panel header, next to the h3.** Subtle, encoded in the existing typography rhythm, and naturally extends the eyebrow's small-text treatment. The pill is the only new shape; everything else (border, surface, h3) is unchanged.

We pick the pill. The pill uses the same five status tokens the rest of the design system already uses for status surfaces (pulse-green for `success`, signal-teal for `partial`, coral-red for `error`, ash/graphite for `neutral`/`empty`). A new shared CSS class `.status-pill` plus modifier classes `.status-pill-{variant}` keeps the look consistent with the existing `feedback-message-*` pattern.

### Decision 3: Status pill variants are derived in the component, not added to the API

The status pill needs three inputs: `label` (short word) + `variant` (success / partial / error / neutral / loading). The component computes these from the same props the panel already receives — there is no new server field or API change.

- **Signal panel:** `success` if `signal` is present and `status === "success"`, `partial` if `status === "partial"`, `error` if `status === "failed"`, `neutral` if `signal` is `null`/`undefined`, `loading` while the dashboard is loading.
- **Backtest panel:** `success` if a recent backtest exists with `status === "success"`, mirrors the backtest status otherwise, `neutral` if no backtest exists, `loading` while loading.
- **Fetches panel:** `success` if the latest log row is `success`, `partial` if `latest.status === "partial"`, `error` if `latest.status === "failed"`, `neutral` if the log list is empty, `loading` while loading.

Labels are short, declarative verbs/nouns: `Active`, `Partial`, `Errors`, `No data`, `Loading` — five values total. No new copy invention, no new icons.

### Decision 4: Empty state changes scoped to `.dashboard-panel .empty-state` only

The shared `<EmptyState>` component is consumed by other pages (Signal Detail, Backtest Detail) and by other dashboard surfaces (`market-empty-state`). We do not modify the component. Instead, we add a scoped CSS rule:

```css
.dashboard-panel .empty-state {
  background: transparent;
  border: 1px dashed var(--color-graphite);
  color: var(--color-fog);
  padding: var(--spacing-20) var(--spacing-16);
}
```

This is contained to dashboard workflow panels and leaves `EmptyState` consumers elsewhere untouched. The detail pages, the operations error/feedback states, and the signal-empty-action call-to-action are not affected.

### Decision 5: FetchLogSummary entry shape — compact 2-row div, native `<details>` for errors

We considered two alternative shapes for the log entry:

- **Keep the `dl`, but compress to 3 rows and use a CSS `text-overflow: ellipsis` on the error cell.** Smaller change, but the resulting cell is still a long uncollapsible string and the cell's value-vs-label alignment fights the rest of the page.
- **Switch to a `div`-per-entry shape: row 1 = mono timestamp + status pill, row 2 = `Fetched / Inserted / Updated` separated by middle dots, error under `<details>`.** Lighter, renders 60–80px per entry (down from ~160px), and the native `<details>` element gives accessible, JS-free expand/collapse.

We pick the second. The fetch log already lives inside `.fetch-log-list` which is `max-height: 320px; overflow-y: auto`; switching the entry shape gets ~3 entries into the visible area at desktop, which is enough to scan recent history without expanding the panel. A thin custom scrollbar on `.fetch-log-list` (`scrollbar-width: thin` + a hairline `::-webkit-scrollbar` styled in `--color-graphite` over `var(--surface-obsidian)`) keeps the boundary visually quiet.

## Risks / Trade-offs

- **Heading-text test breakage in `App.test.tsx`.** 12 existing assertions match headings by string (`getByRole("heading", { name: "Latest signal" })`, etc.). Mitigation: update those assertions to the new single-word titles in the same change; add `data-testid` on each panel as a stable handle for any future tests that need to address the panel without depending on the heading text.
- **Status pill could regress to "decorative ornament" if applied to every panel by default.** Mitigation: the pill is always present and always derived from real panel state — loading, populated, empty, and error states each map to a specific variant. There is no "default pill" path.
- **Native `<details>` does not animate.** Acceptable: the change avoids motion on principle (existing design system does not use reveal animations) and `<details>` is keyboard-accessible by default.
- **Compact fetch log drops the "Mode" field from each row.** Mitigation: mode is implied by the fetch's `status` and is shown when the user opens a backtest or signal detail; if a future need arises, mode can be surfaced as a third micro-row without redesigning the entry shape.
- **Empty-state dashed border may read as "broken" to users coming from the current filled-box treatment.** Mitigation: keep the empty-state text identical to today and add a one-line `aria-live` status pill in the panel header, so the panel still announces "No data" without relying on the empty-state surface alone.

## Migration Plan

This is a frontend-only visual change with no data or API surface. Rollout is a single `npm --prefix apps/web run build` followed by serving the new `apps/web/dist/`. There is no DB migration, no versioned API change, and no dependency bump.

Rollback: revert the commit, rebuild. Because the change is scoped to `DashboardPage.tsx`, `styles.css`, and `App.test.tsx`, a single `git revert` restores the prior behavior.

## Open Questions

None. The design constraints (existing tokens, scoped CSS, single-word titles, native `<details>`) leave no decision for the implementer.
