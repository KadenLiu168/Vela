## Why

The T2.1 `design-system-token-foundations` change shipped new
tokens (`--space-*` ladder, `--text-14/16/17`, `--leading-*` at 1.5,
`--font-feature-settings-default`, and the `--card-*` family) but
intentionally stopped at the declaration line — it did not migrate
any existing CSS or React consumers. Five Initiative issues from
the same `F-3xx` family are now blocked only on this migration work:

- **F-103 Radius → Component mapping; remove capsule shape from nav**
  — `.app-nav-link` still uses `border-radius: var(--radius-pills)`
  (the "capsule" shape). The 8px-grid spacing ladder shipped in T2.1
  added semantic intent; the radius ladder has no analogous mapping
  document and the nav pill is one visible symptom of that gap.
- **F-106 Use `--feedback-accent-*` tokens for all status surfaces**
  — the `.status-pill-*` family still hardcodes raw palette colors
  (`--color-pulse-green`, `--color-signal-teal`, `--color-coral-red`,
  `--color-ash`). The `design-system` capability already requires
  feedback accents to come from `--feedback-accent-*` tokens
  (Requirement: "feedback accents resolve to the named palette
  tokens"); the four status-pill selectors are non-conforming with
  that rule.
- **F-201 Hero heading responsive ladder (48 → 64 → 72)** —
  `.dashboard-heading h1` uses `font-size: clamp(var(--text-heading),
  6vw, var(--text-display))` (a fluid ramp). The design intent is a
  discrete three-step ladder at 48 / 64 / 72 px. The fluid clamp
  misses the 64 px "tablet" rung entirely and produces non-canonical
  intermediate values between the steps.
- **F-2.2 Replace `line-height: 1` magic value in `styles.css`** — the
  pre-existing magic `line-height: 1;` on `.app-nav-link` and the
  `line-height: 1.4;` on `.workflow-grid strong, .detail-page dd`
  violate the T1 line-height-token rule.
- **F-3A.9 `EmptyAction` accepts a `variant` prop** — the
  component-level function (currently inline in `DashboardPage.tsx`)
  hardcodes `className="button-secondary"` on its rendered `<button>`,
  so any future caller that needs a primary-CTA empty-state cannot
  reuse it.

These five items share one shape: "consume the tokens T2.1 shipped
and the rules the `design-system` capability already states". They
are independent enough to commit separately but cohesive enough that
reviewing them in one change keeps the design-system surface honest.

## What Changes

- **F-103 — Nav loses its capsule; radius mapping is documented**:
  - `apps/web/src/styles.css`: `.app-nav-link` `border-radius`
    changes from `var(--radius-pills)` to `var(--radius-md)` (a soft
    tile). `:hover` background already non-accent; no other style
    change.
  - `openspec/specs/design-system/spec.md`: add a Requirement
    "Radius → component mapping is canonical" with one Scenario that
    pins the mapping (Card → `--radius-cards`, Button →
    `--radius-buttons`, Input → `--radius-inputs`, Badge →
    `--radius-badges`, Pill → `--radius-pills`).
- **F-106 — Status pills consume `--feedback-accent-*`**:
  - `apps/web/src/styles.css`: `.status-pill-success` → use
    `var(--feedback-accent-success)` (replacing `--color-pulse-green`).
  - `.status-pill-partial` → use `var(--feedback-accent-info)`
    (replacing `--color-signal-teal`).
  - `.status-pill-error` → use `var(--feedback-accent-error)`
    (replacing `--color-coral-red`).
  - `.status-pill-neutral` → use `var(--feedback-accent-empty)`
    (replacing `--color-ash`). **Visual change**: neutral pills
    darken from `--color-ash` (`#62666d`) to `--color-smoke`
    (`#383b3f`). This is intentional — `--feedback-accent-empty`
    is the canonical empty / muted state per the existing
    `design-system` spec, and neutral status pills are exactly that.
- **F-201 — Dashboard heading ladder**:
  - `apps/web/src/styles.css`: `.dashboard-heading h1` `font-size`
    changes from `clamp(var(--text-heading), 6vw, var(--text-display))`
    to a discrete ladder:
    - default (mobile): `var(--text-heading)` (48 px)
    - `@media (min-width: 768px)`: `var(--text-heading-lg)` (64 px)
    - `@media (min-width: 1280px)`: `var(--text-display)` (72 px)
  - The mobile `@media` override block (around `styles.css:1269`) that
    re-pins `.dashboard-heading h1` to `var(--text-heading)` becomes
    redundant once the base value is `var(--text-heading)`. It is
    removed to avoid a conflicting declaration.
- **F-2.2 — Two magic line-heights become tokens**:
  - `apps/web/src/styles/tokens.css`: declare
    `--leading-snug: 1.4;` (placed in the "4. Typography scale"
    group alongside `--leading-body`).
  - `apps/web/src/styles.css`: `.app-nav-link { line-height: 1; }` →
    `var(--leading-heading)` (resolves to `1`, identical runtime).
  - `apps/web/src/styles.css`:
    `.workflow-grid strong, .detail-page dd { line-height: 1.4; }` →
    `var(--leading-snug)`.
- **F-3A.9 — `EmptyAction` accepts a `variant` prop**:
  - `apps/web/src/pages/DashboardPage.tsx`: extend the inline
    `EmptyAction` function signature with a `variant` prop
    (`"button-secondary" | "button-primary" | "button-tertiary"`,
    default `"button-secondary"`). The rendered `<button>`'s
    className becomes `` `${variant}` ``. The existing two call
    sites (lines 263, 629) keep the default — no behavior change at
    those sites.
- **Spec**:
  - `design-system` capability gains two Requirements:
    1. *Radius → component mapping is canonical* (F-103)
    2. *Dashboard heading uses a discrete responsive ladder*
       (F-201 — pins the 48 / 64 / 72 / breakpoint values)
  - `web-frontend-app` capability gains one Requirement:
    *`EmptyAction` is variant-aware* (F-3A.9 — pins that the
    component advertises its variant).
  - No new Requirement for F-106 because the existing
    "feedback accents resolve to the named palette tokens"
    Requirement already enforces it; the four pill migrations
    are pure code conformance.
  - No new Requirement for F-2.2 because the existing "Line-height
    MUST come from a `--leading-*` token" Requirement already
    enforces it; the two line-height migrations are pure code
    conformance.

No new component files, no new dependencies, no API changes.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `design-system`:
  - **ADDED** Requirement: *Radius → component mapping is canonical*
    (F-103). Locks the radius each component family uses; documents
    the fact that `.app-nav-link` is **not** a pill.
  - **ADDED** Requirement: *Dashboard heading uses a discrete
    responsive ladder* (F-201). Pins the 48 / 64 / 72 px / 768 / 1280
    px breakpoints.
  - The "feedback accents resolve to the named palette tokens"
    Requirement is already in place (added in T1); this change's
    four pill migrations bring the code into conformance.
  - The "Line-height MUST come from a `--leading-*` token"
    Requirement is already in place (added in T1); this change's
    two line-height migrations bring the code into conformance.
- `web-frontend-app`:
  - **ADDED** Requirement: *`EmptyAction` advertises its variant*.
    Pins that the component-level `EmptyAction` function takes a
    `variant` prop and renders the corresponding
    `.button-{primary,secondary,tertiary}` className, matching the
    "Buttons declare their variant via className" rule in
    `design-system`.

## Impact

- **Files**:
  - `apps/web/src/styles.css` — `.app-nav-link` (radius + line-height),
    4 `.status-pill-*` selectors, `.dashboard-heading h1` + the
    mobile override block, `.workflow-grid strong, .detail-page dd`.
    Net ~15 lines changed / 1 block deleted.
  - `apps/web/src/styles/tokens.css` — one new declaration
    (`--leading-snug: 1.4;`).
  - `apps/web/src/pages/DashboardPage.tsx` — `EmptyAction` function
    signature + JSX className (4-line change in function body;
    call sites unchanged).
  - `openspec/specs/design-system/spec.md` — 2 new Requirements
    (radius mapping + dashboard ladder) + their scenarios.
  - `openspec/specs/web-frontend-app/spec.md` — 1 new Requirement
    (EmptyAction variant-aware) + scenarios.
- **Risks**:
  - `.status-pill-neutral` darkens (visual change). Flagged above;
    flagged again in commit body. This is the canonical empty /
    muted state per the spec; risk is aesthetic, not functional.
  - Dashboard heading ladder is discrete instead of fluid. Risk:
    between 768–1280 px viewport widths the heading is locked at
    64 px (no growth). This is the design intent; risk is that
    intermediate widths look slightly small for very wide tablet
    displays. Mitigation: spec pins the breakpoints; future change
    can add intermediate steps if needed.
  - `.app-nav-link` losing its capsule is a small but visible
    visual change. Risk: reviewers may want to keep the pill. The
    change is irreversible via spec rule; if reviewers object, the
    change should be reconsidered before archive.
