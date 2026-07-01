## Context

The web app already has a client-side Signal Detail route, but it renders placeholder content for a demo signal id. COP-99 added `GET /api/strategy-signals/latest`, returning either a latest successful signal payload or a stable empty state.

COP-101 should convert the placeholder into a real latest signal detail page without changing backend behavior or adding candidate ranking diagnostics.

## Goals / Non-Goals

**Goals:**

- Load latest signal data through the shared frontend API client.
- Render signal date, config version, result, fallback status, and generated timestamp from the API response.
- Render a clear local empty state when `has_signal` is false.
- Keep the route and implementation small enough for the current first-phase frontend.

**Non-Goals:**

- No candidate ranking diagnostics.
- No signal generation action on the detail page.
- No backend API or database changes.
- No historical signal selector or date filter.

## Decisions

- Use `GET /api/strategy-signals/latest` through `apps/web/src/api/client.ts`.
  - Rationale: COP-99 established the structured latest signal API and empty-state semantics.
  - Alternative considered: derive detail data from `GET /api/dashboard`; rejected because dashboard only exposes a summary and does not represent the structured latest signal API contract.

- Keep the existing `/signals/demo-signal` route working but make the rendered page latest-signal based.
  - Rationale: the current app shell navigation already points at this route, and COP-101 asks for latest signal detail rather than a specific historical signal id.
  - Alternative considered: add `/signals/latest`; rejected for this COP because it would require route/nav surface changes beyond the placeholder replacement.

- Display only final signal metadata in the first version.
  - Rationale: the issue notes explicitly exclude candidate ranking diagnostics.
  - Alternative considered: render positions and ranking values; rejected as broader than the COP-101 acceptance criteria.

## Risks / Trade-offs

- Existing route name still includes a demo id -> Mitigation: keep route compatibility but remove visible demo-id semantics from the page content.
- API failure can look similar to empty data if copy is vague -> Mitigation: render separate loading, error, populated, and empty states.
