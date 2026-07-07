## Why

The F-107 Initiative issue asks for an "Empty / Loading / Skeleton /
Error component set" — a coherent, reusable family of state-UI
primitives that the Dashboard, Signal Detail, and Backtest Detail
pages can reach for instead of inlining the same patterns.

The current state is partial:

- `apps/web/src/components/FeedbackMessage.tsx` exports
  `FeedbackMessage` (a `<div role="status" | "alert">` wrapper
  with `loading | success | error | info` variants) and
  `EmptyState` (a `<p class="empty-state">` wrapper). Both are
  consumed by all three page files via
  `import { EmptyState, FeedbackMessage } from "../components/FeedbackMessage"`.
- **Skeleton** does not exist anywhere. Every "loading" state today
  renders a text message ("Loading dashboard data.", "Loading latest
  signal.", etc.) rather than a placeholder shape.
- **ErrorBoundary** does not exist. A render-time exception in
  any page would currently take down the whole route with no
  fallback UI.

The half-built state surface is also organized around a single
file (`FeedbackMessage.tsx`) that exports two visually unrelated
components. There is no barrel — every page imports from the deep
path. The empty / loading / error concerns are not separable at the
import boundary.

This change fills the gaps (Skeleton + ErrorBoundary), introduces a
canonical barrel (`apps/web/src/components/index.ts`), and adds the
two missing CSS primitives (`.skeleton` pulse animation and
`.error-boundary` fallback) without changing any existing
component's public API.

## What Changes

### New components

- **`apps/web/src/components/Skeleton.tsx`** — a placeholder
  primitive. Renders a `<span>` (or `<div>` when `as="block"`) with
  the `.skeleton` class, configurable `width` (default `"100%"`),
  `height` (default `"0.75em"`), and `variant` (`"text" | "block"`
  with `text` defaulting to inline span and `block` to a block-level
  div). The element has a pulse animation that respects
  `prefers-reduced-motion: reduce` (animation freezes to a flat
  surface when the user prefers no motion, per the existing
  `Motion vocabulary declared and respected` Requirement).
- **`apps/web/src/components/ErrorBoundary.tsx`** — a React class
  component (the only class-component requirement in React's
  error-boundary API). Catches render-time exceptions in its
  `children` subtree and renders an `<EmptyState>`-shaped fallback
  (uses `<FeedbackMessage variant="error">` internally) when a
  child throws. Accepts an optional `fallback` prop (a React node)
  for custom error UIs; default fallback is the canonical
  FeedbackMessage error surface.
- **`apps/web/src/components/index.ts`** — a barrel module that
  re-exports `EmptyState`, `FeedbackMessage`, `Skeleton`, and
  `ErrorBoundary`. The existing `FeedbackMessage.tsx` keeps its
  named exports so deep-path imports still work; new code MUST
  import from the barrel.

### CSS additions

In `apps/web/src/styles.css`:

- `.skeleton` — base styling: `display: inline-block`,
  `background: var(--surface-obsidian)`, `border-radius: 2px`,
  `min-width: 4em` (so an empty skeleton is still visible).
- `.skeleton-pulse` — adds `animation: skeleton-pulse 1.4s ease-in-out
  infinite` (declared with `@keyframes`); opacity goes 1 → 0.55 → 1.
- `@media (prefers-reduced-motion: reduce) { .skeleton-pulse {
  animation: none; opacity: 0.55; } }` — freezes the pulse for
  motion-sensitive users (consistent with the existing global
  prefers-reduced-motion rule).
- `.error-boundary` — wraps the `<FeedbackMessage variant="error">`
  fallback so the boundary itself has consistent vertical
  padding/margin in the AppShell (`margin: var(--spacing-24) 0`).
- The `.skeleton` token references:
  - `--duration-base: 200ms` for the pulse easing
  - `--surface-obsidian` for the placeholder background
  - No new tokens introduced.

### Migration (small, scoped)

- `apps/web/src/pages/DashboardPage.tsx`,
  `apps/web/src/pages/SignalDetailPage.tsx`,
  `apps/web/src/pages/BacktestDetailPage.tsx`: change
  `import { EmptyState, FeedbackMessage } from "../components/FeedbackMessage"`
  to `import { EmptyState, FeedbackMessage } from "../components"`.
  Three line changes, no behavior change.
- `apps/web/src/App.tsx`: wrap the route in
  `<ErrorBoundary>...</ErrorBoundary>`. One block of JSX added.
  No behavior change at runtime (the boundary only activates on
  render errors).

### Spec

- `design-system` capability gains one new Requirement
  *State component set is exported from the components barrel*.
- Two scenarios pin:
  1. the barrel exports `EmptyState`, `FeedbackMessage`,
     `Skeleton`, `ErrorBoundary`;
  2. the Skeleton animation respects `prefers-reduced-motion`.
- The existing `Motion vocabulary declared and respected`
  Requirement is already in place; the new Skeleton rule reuses
  the same `prefers-reduced-motion` mechanism.
- The existing feedback-accent and status-pill rules are already
  in place; the new ErrorBoundary's fallback surfaces a
  `<FeedbackMessage variant="error">` which already conforms.

No new tokens. No breaking changes to existing component APIs.
The two new components (`Skeleton`, `ErrorBoundary`) are additive.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `design-system`: **ADDED** Requirement: *State component set is
  exported from the components barrel*. Pins that
  `apps/web/src/components/index.ts` exports `EmptyState`,
  `FeedbackMessage`, `Skeleton`, and `ErrorBoundary`; pins that
  new code MUST import from the barrel; pins the Skeleton's
  reduced-motion behavior.

## Impact

- **Files**:
  - `apps/web/src/components/Skeleton.tsx` — NEW
  - `apps/web/src/components/ErrorBoundary.tsx` — NEW
  - `apps/web/src/components/index.ts` — NEW (barrel)
  - `apps/web/src/styles.css` — +~30 lines (`.skeleton`,
    `.skeleton-pulse`, `@keyframes`, prefers-reduced-motion
    override, `.error-boundary`).
  - `apps/web/src/pages/DashboardPage.tsx` — 1 import line
  - `apps/web/src/pages/SignalDetailPage.tsx` — 1 import line
  - `apps/web/src/pages/BacktestDetailPage.tsx` — 1 import line
  - `apps/web/src/App.tsx` — wrap route in `<ErrorBoundary>`
  - `openspec/specs/design-system/spec.md` — 1 new Requirement
    + 2 scenarios.
- **Risks**:
  - **ErrorBoundary changes app render tree**: a render error in
    any page now shows a fallback instead of a blank page.
    Risk: any pre-existing render bug becomes more visible.
    Mitigation: the App tests cover the happy paths; if any test
    is accidentally triggering a render error, it surfaces
    immediately in CI.
  - **Skeleton visual**: 1.4s pulse with opacity dip to 0.55
    is the standard pattern; matches Linear / GitHub / Vercel
    visual conventions.
  - **Import migration is shallow**: 3 lines across 3 files,
    no semantic change. If a future change wants to delete
    `FeedbackMessage.tsx` and force the barrel, that's a
    separate breaking change.
