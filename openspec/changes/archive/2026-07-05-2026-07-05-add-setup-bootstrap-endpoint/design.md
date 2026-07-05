## Context

Vela's local setup currently has three independent entry points:

- `uv run vela init-db` -- applies Alembic migrations to bring the local SQLite database to the current head revision.
- `uv run vela sync-etf-pool` -- loads `config/strategy_v1.yaml` (and the ETF pool it references) and upserts `ETFInfo` rows.
- Dashboard "Full fetch" button or `uv run vela fetch-market-data` -- reads `ETFInfo.is_active = true`, fetches the full daily history, and upserts `MarketPrice` rows.

The Dashboard only exposes the third step, and its label claims it is for "initialization or repair" even though the underlying endpoint fails on an empty database. The compound operation has been a long-standing "wouldn't it be nice" -- the three steps are individually idempotent and well-bounded, so chaining them is mechanical.

## Goals / Non-Goals

**Goals:**

- Add a single Dashboard action that takes a fresh local database to a fully populated state.
- Reuse the existing init-db, sync-etf-pool, and full fetch workflows without modifying them.
- Surface per-step status so a user can see which step ran and which step failed.
- Keep the change scoped to the Web Dashboard; the CLI commands stay as-is for ops and debug.

**Non-Goals:**

- Do not modify `init-db`, `sync-etf-pool`, or full fetch behavior.
- Do not add background jobs, scheduling, or polling.
- Do not turn the API service into a production schema-management process; the new endpoint is local-development only.
- Do not introduce a new ETF pool model or new persistence tables.
- Do not duplicate business logic in the API entrypoint.

## Decisions

1. Orchestrate inside a new `vela_core.bootstrap` module, not in the API route handler.

   Rationale: the orchestrator coordinates three workflows that already live in core. Keeping the chain in core makes it testable with the same fake-provider pattern that the existing fetch tests use, and the API layer only translates HTTP to a single function call.

   Alternative considered: chain the three calls inside the FastAPI route handler. Rejected because it would mix HTTP concerns with the three-step business orchestration and would be hard to unit-test independently.

2. Reuse the API process's already-loaded strategy config.

   Rationale: `/api/config` already returns the loaded strategy summary, which means the config is loaded per request. The bootstrap endpoint needs the same config to call `sync_etf_pool_to_db`. Caching it in `app.state.strategy_config` at startup removes duplication and avoids re-reading the YAML on every bootstrap call.

   Alternative considered: accept the strategy config path as a query parameter on the endpoint. Rejected because it would leak internal file layout to the Web caller and would let the Web call drift from the running API's config.

3. Hard-stop on first failure, do not roll back earlier successful steps.

   Rationale: the three steps are not transactional. Alembic has no native downgrade, ETF sync is intentionally additive (it never deletes rows), and market price upserts are insert-or-update. Reporting which step failed is enough for a developer to fix and re-run.

   Alternative considered: roll back on failure. Rejected because there is no clean rollback boundary -- Alembic does not guarantee a downgrade path, and the user has explicit "preserve rows outside configured pool" semantics on ETF sync.

4. Return a typed `BootstrapResult` with per-step status and a top-level `status` and `failed_step`.

   Rationale: the Web UI needs a deterministic shape to render a three-step status display. Returning a flat list of step results plus an aggregate `status` makes the front end trivial and keeps the API self-describing.

   Alternative considered: return a single top-level `status` and a free-form message. Rejected because the Web UI specifically wants to show "step 2 failed, here is the error", which needs the structured per-step data.

5. Place the new Dashboard button at the right end of the existing action list and render it in the primary (filled) variant.

   Rationale: the existing three action buttons (Fetch market data, Full fetch, Generate signal) are all rendered in the secondary (outline) variant. The bootstrap action is a "primary" setup action that runs more and is more consequential. Placing it at the right and giving it the filled variant visually separates it from the daily-fetch action without introducing a new color.

   Alternative considered: introduce a new "Setup" panel for the bootstrap action. Rejected because the existing action panel already groups one-shot triggers; a new panel would split related actions across the Dashboard.

6. Display each step's status icon and a final total duration; do not display per-step elapsed time.

   Rationale: the first two steps complete in milliseconds; showing "0.05s" for them is noise. The third step is the slow one and its time is captured by the total duration. If a step fails, the step-level error text is the actionable signal, not the elapsed time.

   Alternative considered: show per-step elapsed time on every step. Rejected because the front-end display would be cluttered with low-signal numbers and the total duration already captures the dominant step.

## Risks / Trade-offs

- The bootstrap endpoint runs Alembic inside the API process, which couples the API to the migration scripts directory. -> Document the endpoint as local-development only; Phase 1 deployment is a single-machine dev workflow, so this is acceptable. If Vela grows a multi-process deployment, the bootstrap action will need to move back to the CLI.
- A long-running full fetch can hold the HTTP request open for minutes. -> Use the same in-flight operation lock the Dashboard already uses for the "Full fetch" button; the Web client already tolerates the long round-trip.
- The `sync-etf-pool` step assumes `config/strategy_v1.yaml` (and its referenced ETF pool file) are present and valid. -> A missing or invalid config file surfaces as a failed `sync_etf_pool` step with a clear error message; the bootstrap result reports it and stops.
- Re-running bootstrap on a fully initialized database is a no-op for steps 1 and 2, but step 3 still re-fetches the full history. -> That is the existing "Full fetch" behavior, which is the documented contract for re-syncing local data; the bootstrap action does not introduce new cost beyond what clicking the old "Full fetch" button already incurred.
- The new endpoint shares the same `DataFetchLog` row format as the existing full fetch. -> This is intentional: dashboard and back-office tooling that already reads the log can treat a bootstrap-initiated fetch the same as a manual full fetch.
