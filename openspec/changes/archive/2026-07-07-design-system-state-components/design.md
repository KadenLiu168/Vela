## Context

F-107 calls for an "Empty / Loading / Skeleton / Error component set".
The web frontend today has two of the four:

- `FeedbackMessage` (4-variant banner: loading / success / error / info)
- `EmptyState` (paragraph-shaped empty surface)

What is genuinely missing is **Skeleton** (a placeholder primitive
for content whose shape is known but whose data is still loading)
and **ErrorBoundary** (a render-error fallback). The web frontend
has had zero production render-error protection: a thrown
exception in any page component would unmount the whole AppShell.

A third concern is **organization**: every page imports from a deep
path (`../components/FeedbackMessage`) rather than a canonical
barrel. The new components will be reachable only via the barrel,
so the natural move is to also redirect existing imports to the
barrel.

The constraint surface is unchanged: this change lives at the
component layer (TSX + CSS) and modifies only files owned by the
`design-system` capability and the three page entry points.

## Goals / Non-Goals

**Goals**

- Add the two missing primitives (`Skeleton`, `ErrorBoundary`)
  to round out the Empty / Loading / Skeleton / Error set.
- Add a canonical barrel (`apps/web/src/components/index.ts`)
  and migrate the three page imports to it.
- Add the supporting CSS primitives (`.skeleton`,
  `.skeleton-pulse`, `.error-boundary`) with
  `prefers-reduced-motion` honored.
- Add an explicit Requirement to the `design-system` capability
  pinning the barrel as the canonical import path.

**Non-Goals**

- **Migrating any existing loading text to Skeleton.** The
  existing text-based loading messages ("Loading dashboard data.")
  are working and tested; replacing them with skeleton layouts
  is a UX change that should be its own change. Skeleton is
  shipped as a primitive; consumers adopt incrementally.
- **Extracting `EmptyState` from `FeedbackMessage.tsx`.** The
  file currently houses both, which is mildly ugly, but moving
  one component out of an existing file is a separate refactor
  with no new functionality. Belongs to a follow-up if it ever
  matters.
- **Adding `<ErrorState>` as a top-level component.** The error
  surface today is `<FeedbackMessage variant="error">`, which is
  already a first-class API. The new `ErrorBoundary` reuses that
  surface; no new component is needed for the error visual.
- **Renaming `FeedbackMessage`.** Considered but rejected:
  `FeedbackMessage` is used 25 times across the three pages;
  renaming would be churn for zero behavior change.
- **Generic ErrorBoundary logging / Sentry integration.** Out of
  scope; a future change can layer observability on top of the
  primitive boundary.
- **Testing the Skeleton visually.** No visual regression
  harness exists; the smoke test (TypeScript + Vitest + lint)
  is the only automated gate. Visual verification happens in
  dev server.

## Decisions

### D1. Skeleton renders a `<span>` by default, `<div>` with `as="block"`

```tsx
<Skeleton />                            // inline-block span, 100% × 0.75em
<Skeleton width="20em" />               // inline span, 20em × 0.75em
<Skeleton as="block" height="12em" />   // block div, 100% × 12em
<Skeleton variant="circle" diameter="3em" />
```

**Rationale.** Most Skeleton usage is inline (a word placeholder
inside a sentence or a single line placeholder inside a panel).
Defaulting to `<span>` keeps the layout flow correct without
forcing callers to remember `as="block"`. The `variant="circle"`
form is for avatar / icon placeholders.

**Alternatives considered.**

- *Always render `<div>`. * Rejected: forces every caller to
  worry about layout flow.
- *Always render `<span>`. * Rejected: block-level Skeletons
  (full-row placeholders) need to participate in grid /
  flex layouts as block elements.

### D2. Skeleton pulse is opacity, not background-color

```css
@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.55; }
}
```

**Rationale.** Opacity is cheap (no repaint), GPU-accelerated,
and respects the existing color tokens (`--surface-obsidian`
provides the base; the pulse modulates alpha only). The 0.55
minimum is high enough to keep the placeholder readable but
low enough to feel alive.

**Alternatives considered.**

- *Animate `background-color` between two palette tokens.* Rejected:
  forces new tokens (or a hardcoded secondary color); less
  GPU-friendly.
- *A shimmer sweep (a moving gradient).* Rejected: looks great
  but is more code, more tokens (the gradient stops), and harder
  to test visually. Out of scope.

### D3. ErrorBoundary reuses `<FeedbackMessage variant="error">` for the fallback

```tsx
<ErrorBoundary fallback={<FeedbackMessage variant="error">…</FeedbackMessage>}>
  …
</ErrorBoundary>
```

The default fallback (no `fallback` prop passed) renders the
canonical error surface.

**Rationale.** The error visual contract is already defined
(`feedback-message-error` styling, accent border, ARIA `role="alert"`).
Reusing it keeps the visual language consistent and means the
new ErrorBoundary adds zero new visual contract surface.

**Alternatives considered.**

- *A bespoke `.error-boundary` block.* Rejected: duplicates the
  FeedbackMessage error styling. The `.error-boundary` wrapper
  class only adds outer margin so the boundary looks right
  inside the AppShell.

### D4. Barrel at `apps/web/src/components/index.ts`, existing file unchanged

`index.ts` re-exports `EmptyState` and `FeedbackMessage` from
their current location; new code imports from the barrel.
Existing direct imports from `../components/FeedbackMessage`
continue to resolve (no breaking change).

**Rationale.** The barrel is the canonical path going forward,
but the existing file is not deleted in this change. This keeps
the diff small and the migration reversible. A future change can
delete `FeedbackMessage.tsx` and force the barrel once consumers
have migrated.

**Alternatives considered.**

- *Move `EmptyState` to its own file now and have `FeedbackMessage.tsx`
  re-export for back-compat.* Considered but rejected: the
  refactor has no new behavior and would expand the diff for
  zero review value.

### D5. ErrorBoundary wraps the route in `App.tsx`, not individual pages

```tsx
<ErrorBoundary>
  {renderRoute(path)}
</ErrorBoundary>
```

**Rationale.** A single boundary at the App root catches render
errors in any page without per-page wrapping. The fallback is
positioned inside the AppShell `<main>` so layout chrome
(header, nav) survives. This is the minimum-viable error
protection; per-page boundaries can be added later for
fine-grained recovery.

**Alternatives considered.**

- *Per-page boundaries.* Rejected for this change: more code,
  no behavior improvement over the App-root boundary for the
  current 3-page app.
- *No boundary at all.* Rejected: F-107 explicitly lists Error
  as one of the four required components.

### D6. Skeleton does not add a new token

The Skeleton's pulse reuses `--surface-obsidian` (placeholder
fill) and the existing motion vocabulary (`--duration-base`).
No new tokens are introduced.

**Rationale.** Token additions are governed by their own
OpenSpec changes (T2.1 added `--leading-snug`; a Skeleton
introducing a `--skeleton-color` would be a token-level change
on its own). The placeholder color is `--surface-obsidian`
because the placeholder sits on a `--surface-carbon` (status
surface) background, and the obsidian tone reads as
"loading" without needing a dedicated token.

**Alternatives considered.**

- *Add `--skeleton-bg`, `--skeleton-pulse-min`, etc.* Rejected:
  speculative; current primitives are sufficient.

## Risks / Trade-offs

- **ErrorBoundary visibility** — render errors that were
  previously silent (or only console-visible) now surface a
  fallback. → Mitigation: existing tests cover happy paths;
  render-error tests are an explicit gap and a known follow-up.
- **Three shallow import changes** — `App.test.tsx` queries
  the EmptyState by className, which is unchanged by the import
  migration. → Mitigation: grep confirms test assertions still
  resolve.
- **Pulse animation in low-power mode** — the
  `prefers-reduced-motion` block freezes the pulse to opacity
  0.55 (a flat dimmed surface). This is intentional but
  slightly different from "no animation" (the surface still
  has the dimmed appearance, which some users might prefer to
  be at full opacity). → Mitigation: spec pins the exact
  behavior; future tweak is a one-line change.
- **Header-text whitespace mismatch on archive-time merge** →
  Mitigation: spec uses only ADDED Requirements with new
  unique names, so no existing header needs verbatim re-typing.
