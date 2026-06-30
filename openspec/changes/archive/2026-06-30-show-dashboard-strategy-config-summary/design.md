## Context

The API already exposes the current strategy configuration through `GET /api/config`, and `GET /api/dashboard` reuses the same YAML-backed serialization for its `strategy` field. The Dashboard page currently calls `getDashboard()` through the shared frontend API client and renders a Strategy panel, but that panel only shows a subset of the configuration needed by COP-89.

## Goals / Non-Goals

**Goals:**

- Render a complete read-only strategy configuration summary on the Dashboard using the existing dashboard aggregate response.
- Show strategy id/version, momentum windows, score weights, Top N, defensive asset, and transaction cost summary.
- Validate the behavior through frontend tests using dashboard API response data.

**Non-Goals:**

- Do not add a configuration editor or any mutation path.
- Do not change the backend config schema, YAML files, or dashboard endpoint shape.
- Do not add new routes, dependencies, or database behavior.

## Decisions

- Use `GET /api/dashboard` as the only Dashboard data source.
  - Rationale: the Dashboard already depends on the aggregate API, and that API already passes through the real config summary loaded from YAML. Calling `GET /api/config` separately would duplicate data fetching and create a second loading/error path without adding required coverage.
  - Alternative considered: load `/api/config` from the Strategy panel. This was rejected because COP-89 only needs current Dashboard display and the aggregate endpoint already contains the required real config data.

- Keep formatting in the page component with small helper functions.
  - Rationale: the required summaries are simple display transformations over existing API fields. A new abstraction would add more surface area than value for a single panel.
  - Alternative considered: introduce a reusable StrategySummary component. This can wait until another page needs the same presentation.

## Risks / Trade-offs

- API field shapes are typed as nested config objects in the frontend, but backend serialization is still dict-based.
  - Mitigation: define the specific TypeScript object shapes required by the Dashboard and cover them with rendering tests.
- Numeric values can arrive as numbers from JSON and should be displayed compactly.
  - Mitigation: format score weights and transaction cost values without changing the API contract.
