## Context

`npm --prefix apps/web run lint` currently fails because several route pages synchronously set loading state at the beginning of `useEffect`. The affected pages already have loading state as their initial state, but they also reset to loading synchronously when route parameters, pagination, or price range changes.

`npm --prefix apps/web run lint:css` currently fails because `apps/web/src/styles.css` still contains literal `line-height` and `border-radius` values in rules covered by the existing Stylelint design-system invariants.

## Goals / Non-Goals

**Goals:**

- Make `npm --prefix apps/web run lint` pass without suppressing React hook lint rules.
- Make `npm --prefix apps/web run lint:css` pass without weakening Stylelint rules.
- Preserve current loading, error, empty, and ready UI behavior for affected pages.
- Use existing design tokens for CSS lint fixes.

**Non-Goals:**

- Change API endpoints, response contracts, or data fetching behavior.
- Introduce new design tokens or Stylelint rule changes.
- Redesign loading states or add broader state-management abstractions.
- Modify the AppShell heading change beyond whatever is already staged in the separate archived change.

## Decisions

1. **Avoid synchronous effect state updates by deriving loading on request key changes.**
   - Rationale: the lint failures are caused by direct `setState({ status: "loading" })` calls inside effects. The root cause is that each page stores only the request result, not which request key produced it. Adding the request key to state lets render treat stale results as loading while the new request is pending, without synchronously setting state inside the effect body.
   - Alternative considered: wrap `setState` in a microtask or timeout. Rejected because that hides the lint symptom instead of modeling request freshness.
   - Alternative considered: disable the ESLint rule. Rejected because the repository expects lint gates to enforce the invariant.

2. **Use existing tokens for CSS literals.**
   - Rationale: the design-system spec already requires line-height and border-radius values to route through tokens. Existing tokens should be reused instead of adding new ones.
   - Alternative considered: relax Stylelint. Rejected because the rule is intentional and documented.

## Risks / Trade-offs

- **Risk: stale data could remain visible while a new request is pending.** → State must include the request key, and render must treat any state whose key does not match the current request key as loading.
- **Risk: type complexity increases.** → Keep request keys narrow and local to each page (`offset`, `id`, or `id:range`) rather than introducing shared abstractions.
- **Risk: token substitution changes visual output.** → Choose tokens whose resolved values match the existing literals whenever available.
