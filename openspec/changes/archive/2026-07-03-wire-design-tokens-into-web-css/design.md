## Context

The repository already includes a design reference (`DESIGN.md`), structured tokens (`tokens.json`), and a CSS custom-property snapshot (`variables.css`). The web app currently defines its global styling directly in `apps/web/src/styles.css` with hard-coded colors, spacing, radius, font, and surface values. COP-129 establishes the shared visual foundation for later frontend visual issues without changing application behavior.

## Goals / Non-Goals

**Goals:**

- Expose the provided design colors, fonts, type scale, spacing, layout, radius, and surface tokens from `apps/web/src/styles.css`.
- Align base document styling with the token foundation: page background, text color, font family, and box sizing.
- Prefer token references for direct, low-risk replacements in existing global CSS.
- Keep the rendered UI close to the current layout and avoid route, DOM, API, or behavior changes.

**Non-Goals:**

- No token build pipeline, Style Dictionary integration, PostCSS token transform, or new UI framework.
- No page or component redesign beyond safe base-style alignment.
- No replacement of functional success, error, warning, or info colors unless the design tokens provide a direct semantic equivalent.
- No changes to API calls, routing, data fetching, or backend code.

## Decisions

1. Store the token foundation directly in `apps/web/src/styles.css`.
   - Alternative: import `variables.css` from the app or add a build step from `tokens.json`.
   - Rationale: the issue explicitly asks for `styles.css` to contain the definitions and excludes introducing a token pipeline. Direct custom properties are the smallest verifiable change.

2. Extend the existing `web-frontend-app` capability.
   - Alternative: introduce a new `design-system` capability.
   - Rationale: this issue is scoped to the existing web app's global stylesheet. A separate design-system capability would expand the boundary before reusable components or a broader system exist.

3. Preserve unmatched semantic state colors.
   - Alternative: map all state colors to Ember Orange, Brass, or neutral tokens.
   - Rationale: the provided tokens define brand, neutral, and surface roles, not a full status palette. Preserving existing state color behavior reduces risk and keeps status meaning clear.

4. Validate through existing frontend and OpenSpec commands.
   - Alternative: add CSS-variable unit tests.
   - Rationale: current tests focus on React behavior and rendered content. CSS variable assertions would couple tests to implementation details without improving acceptance coverage for this base stylesheet change.

## Risks / Trade-offs

- Global CSS inheritance could shift colors or typography more than intended -> mitigate by changing base rules and direct token mappings only, leaving component structure and unmatched status colors intact.
- Duplicating token values from `variables.css` can drift over time -> mitigate by treating `variables.css` and `tokens.json` as the source reference for this one-time COP-129 wiring, with future issues free to add a pipeline if needed.
- Some existing hard-coded colors may remain after COP-129 -> acceptable where no direct token equivalent exists or changing them would become visual redesign rather than token foundation wiring.
