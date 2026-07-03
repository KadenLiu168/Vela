## Context

`FeedbackMessage` already centralizes loading, info, success, and error roles, while Dashboard and detail pages also use `.empty-state` and `.dashboard-load-state-*` for related state presentation. Previous visual work moved Dashboard feedback away from broad chromatic blocks, but shared empty states and detail-page status states still rely on scattered selectors.

## Goals / Non-Goals

**Goals:**

- Use existing Graphite, Steel, Slate, Mist, Canvas, Fog, Ivory, Ember, and Brass tokens for shared state presentation.
- Keep loading, error, info, success, and empty states visually related but individually recognizable through narrow accents and neutral surfaces.
- Preserve current `FeedbackMessage` accessibility semantics and page behavior.
- Keep changes limited to COP-135 presentation scope.

**Non-Goals:**

- No API, route, state-machine, data-loading, error categorization, or business-logic changes.
- No skeleton loaders, toast system, large UI framework, or new dependency.
- No copy-meaning changes for existing loading, empty, or error messages.

## Decisions

1. Reuse the existing shared `FeedbackMessage` component.
   - Rationale: It already owns `role="alert"` for errors and `role="status"` for non-errors.
   - Alternative considered: create separate `EmptyState` or `StatusBadge` components. Rejected because COP-135 can be satisfied with smaller CSS and class reuse.

2. Represent statuses with neutral surfaces and narrow accent rails.
   - Rationale: `DESIGN.md` requires a mostly achromatic interface with Ember and Brass used sparingly.
   - Alternative considered: per-status filled backgrounds. Rejected because broad blue, green, or red blocks are explicitly out of scope.

3. Make `.empty-state` a shared tokenized state surface and use modifiers only where layout differs.
   - Rationale: Dashboard, Signal Detail, and Backtest Detail already render empty states through this class.
   - Alternative considered: page-specific empty-state styling. Rejected because it preserves the inconsistency COP-135 is meant to reduce.

## Risks / Trade-offs

- Shared `.empty-state` changes can affect several panels at once -> Keep the base treatment compact and neutral, and preserve existing page-specific spacing overrides.
- Visual consolidation without new component APIs limits semantic differentiation -> Use existing `FeedbackMessage` variants for ARIA-bearing statuses and use shared CSS for non-ARIA empty text.
- Existing tests mostly assert text and ARIA roles rather than CSS -> Add focused presentation/semantic checks where they can detect class/role regressions without coupling to exact colors.
