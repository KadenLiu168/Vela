## Context

Vela already stores market data fetch workflow runs in `DataFetchLog` and the Dashboard already loads first-screen state through `GET /api/dashboard`. The current Dashboard shows market price coverage and the immediate result of a fetch action, but it does not show recent persisted fetch history after reload.

## Goals / Non-Goals

**Goals:**
- Show recent market data fetch log records on the Dashboard.
- Derive the data from real `DataFetchLog` rows in SQLite.
- Include fetch time, mode, status, row counts, and error summary.
- Keep the UI compact and first-phase appropriate.

**Non-Goals:**
- Do not add a standalone log center.
- Do not add filtering, pagination, search, or drill-down pages.
- Do not change fetch workflow persistence semantics.
- Do not add database schema changes.

## Decisions

1. Extend the existing Dashboard aggregate instead of adding a new route.
   - Rationale: Dashboard already owns first-screen operational state and has request-scoped database access through the API. A separate endpoint would add another frontend loading path without a stronger contract.
   - Alternative considered: `GET /api/market-data/fetch-logs`. Rejected for COP-97 because it starts a separate log surface and invites filtering/pagination scope.

2. Query recent `DataFetchLog` rows in core aggregation.
   - Rationale: The API entrypoint should continue delegating database read-model behavior to `vela_core`.
   - Ordering: newest by `finished_at`, then `started_at`, then id. Running rows without `finished_at` can still appear by start time.

3. Return a small list with existing log fields only.
   - Rationale: Acceptance criteria only need fetch time, mode, status, row counts, and error summary. Existing fields cover this without schema changes.
   - Limit: keep a fixed small number of recent rows to avoid a log center shape.

## Risks / Trade-offs

- Extra Dashboard query cost -> Limit the query to a small number of recent rows and select only `DataFetchLog` records.
- Ambiguous time for running logs -> Use `finished_at` when available and `started_at` as fallback for display.
- Long provider errors can dominate the panel -> Render a summary field in the compact list; detailed log analysis remains out of scope.
