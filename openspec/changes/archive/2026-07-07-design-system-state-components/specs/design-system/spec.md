## ADDED Requirements

### Requirement: State component set is exported from the components barrel
The web frontend MUST expose the Empty / Loading / Skeleton /
Error state-UI primitives as a single named family that is
importable from `apps/web/src/components` (the canonical barrel
at `apps/web/src/components/index.ts`).

The family is:

- **`EmptyState`** — paragraph-shaped empty surface
  (`<p class="status-surface status-surface-empty empty-state">`)
  for "no data yet" or "nothing matches" states
- **`FeedbackMessage`** — banner-shaped status surface
  (`<div role="status" | "alert" class="status-surface
  feedback-message feedback-message-{variant}">`) for the
  `loading | success | error | info` variants
- **`Skeleton`** — placeholder primitive for content whose
  shape is known but whose data is still loading. Renders an
  element with the `.skeleton` class plus optional
  `.skeleton-pulse` animation
- **`ErrorBoundary`** — React class component that catches
  render-time exceptions in its `children` subtree and renders
  a `<FeedbackMessage variant="error">` fallback

All four components MUST be re-exported by
`apps/web/src/components/index.ts`. New code MUST import the
state components from this barrel rather than from the
underlying files.

#### Scenario: barrel exports the four state components
- **WHEN** a developer inspects `apps/web/src/components/index.ts`
- **THEN** the file MUST re-export `EmptyState`,
      `FeedbackMessage`, `Skeleton`, and `ErrorBoundary` as
      named exports
- **AND** any page or test under `apps/web/src/` that needs
      a state component MUST import from
      `"../components"` (or the equivalent relative path that
      resolves to the barrel) rather than from the underlying
      component files

#### Scenario: Skeleton pulse respects prefers-reduced-motion
- **WHEN** the OS reports `prefers-reduced-motion: reduce`
- **THEN** any `<Skeleton>` element with the `.skeleton-pulse`
      class MUST NOT animate (its `animation` property MUST
      resolve to `none` and its `opacity` MUST remain constant)
- **AND** the placeholder MUST still be visually present
      (the surface color and dimensions are preserved)

#### Scenario: ErrorBoundary renders a feedback-message-error fallback on child errors
- **WHEN** a child component passed to `<ErrorBoundary>`
      throws a render-time exception
- **THEN** the boundary MUST render a
      `<FeedbackMessage variant="error">` element (or the
      `fallback` prop if provided) in place of the failing
      subtree
- **AND** the rest of the AppShell (header, nav, main
      layout) MUST continue to render normally

#### Scenario: Skeleton default is inline span
- **WHEN** a `<Skeleton />` element is rendered without props
- **THEN** it MUST render as an inline `<span>` element
- **AND** its rendered width MUST default to `100%` of its
      containing inline context
- **AND** its rendered height MUST default to `0.75em` (one
      line of body text)
