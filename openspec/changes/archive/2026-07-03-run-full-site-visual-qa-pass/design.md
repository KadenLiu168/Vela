## Context

COP-136 is a final frontend visual consistency pass across existing routes and UI states. The current design language is defined by `DESIGN.md`: warm paper surfaces, graphite text, ash/fog/ivory neutrals, sparse ember/brass accents, PolySans headings at regular weight, square buttons, rounded nav pills, and no blue/green admin palette or elevation shadows.

The existing frontend already centralizes tokens in `apps/web/src/styles.css`. No separate `tokens.json` or `variables.css` exists in `apps/web/src`, so this change treats the `:root` custom properties in `styles.css` as the active token source.

## Goals / Non-Goals

**Goals:**
- Verify `/`, `/signals/demo-signal`, and `/backtests/1` in desktop and mobile viewports.
- Keep visual styling consistent with the existing token system and `DESIGN.md`.
- Remove or reduce avoidable hardcoded spacing/typography literals only where they affect the COP-136 surfaces.
- Preserve existing behavior, API calls, routes, and test contracts.

**Non-Goals:**
- No business logic changes.
- No API client changes.
- No route structure changes.
- No new visual direction or broad redesign.
- No large UI framework or new dependency.
- No unrelated technical debt cleanup.

## Decisions

- Keep the implementation CSS-only unless inspection finds a visual issue that CSS cannot address.
  - Alternative considered: component refactors. Rejected because COP-136 is visual QA and route/business structure is explicitly out of scope.
- Use existing CSS variables instead of introducing new token files.
  - Alternative considered: add `tokens.json` or `variables.css`. Rejected because the app already uses `styles.css :root` as the token source and parallel token files would increase drift.
- Prefer small responsive fixes over breakpoint redesign.
  - Alternative considered: new mobile layouts per page. Rejected because current grids already collapse; the risk is edge overflow and inconsistent controls, not missing page architecture.

## Risks / Trade-offs

- Visual QA depends partly on browser inspection and screenshots → Mitigation: check all required routes at desktop and mobile sizes after build.
- Backend-dependent pages may render loading/error states if no API is running → Mitigation: validate layout stability for reachable frontend states and avoid changing API behavior.
- Tight CSS scope may leave unrelated style debt untouched → Mitigation: record out-of-scope follow-up suggestions instead of expanding this COP.
