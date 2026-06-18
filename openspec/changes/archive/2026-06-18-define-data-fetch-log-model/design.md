## Context

Vela already has SQLAlchemy ORM models for ETF metadata and daily market prices, plus Alembic migrations and focused model tests. The next market data foundation gap is observability for fetch jobs: full and incremental runs need a durable record of what source was used, what range was requested, whether the run completed, and what rows or errors resulted.

The current scope is still Phase 1 backend foundation. No ingestion provider clients, scheduler, or repository layer exists yet, so the model should capture enough task-level information for future debugging without assuming a full job orchestration system.

## Goals / Non-Goals

**Goals:**

- Define a `DataFetchLog` ORM model for one market data fetch task.
- Record source, target type, fetch mode, requested date range, requested symbols, status, lifecycle timestamps, result counts, and error message.
- Support debugging full and incremental fetch outcomes.
- Keep storage compatible with the current SQLite-based test setup and SQLAlchemy model style.
- Add targeted indexes for expected inspection paths.
- Add an Alembic migration and focused schema/index tests.

**Non-Goals:**

- Implement market data fetching, provider clients, retry logic, scheduling, or repositories.
- Store provider request or response payloads.
- Track per-symbol or per-date fetch details in a child table.
- Introduce a database enum or JSON-only storage requirement.
- Enforce every possible lifecycle transition at the database layer.

## Decisions

1. Use one log row per fetch task.

   Rationale: Full and incremental runs are naturally task-level operations. A task-level row gives later ingestion code a simple place to record scope, status, counts, and errors.

   Alternative considered: one row per ETF or per provider request. That would improve granular diagnostics, but it adds a detail model before the fetch pipeline exists. If per-symbol diagnostics become necessary, a later `DataFetchLogItem` table can reference the task log.

2. Store fetch scope as `fetch_mode`, `range_start`, `range_end`, and nullable `requested_symbols`.

   Rationale: `fetch_mode` makes full versus incremental debugging explicit, while date range columns support simple filtering. `requested_symbols` preserves the requested universe for investigation without forcing a child table in the first version.

   Alternative considered: infer full or incremental mode from the date range. That is ambiguous because a full run can still have a bounded historical range, and an incremental run can cover multiple missed dates.

3. Store `requested_symbols` as text containing serialized symbol data.

   Rationale: The current project uses SQLite in tests and has no database-specific JSON dependency. Text keeps the model portable while still allowing ingestion code to record the requested universe.

   Alternative considered: use a JSON column. JSON would make provider or symbol filtering easier in some databases, but it is unnecessary for the current debugging goal and can introduce backend-specific behavior.

4. Use string status values: `running`, `success`, `failed`, and `partial`.

   Rationale: These statuses cover active, complete, failed, and mixed-result fetch jobs. `partial` is important for market data because provider failures often affect only part of the requested universe.

   Alternative considered: add `cancelled`, `skipped`, and a database enum immediately. Those may become useful with a scheduler, but they are speculative until cancellation or skip behavior exists.

5. Include result count fields: `rows_fetched`, `rows_inserted`, and `rows_updated`.

   Rationale: Counts make full and incremental fetch results comparable during troubleshooting. They also help distinguish provider empty results from successful no-op upserts.

   Alternative considered: store only status and error text. That is smaller, but it loses the basic quantitative signals needed to diagnose fetch quality.

6. Add indexes for source/status/time and target/mode/range inspection.

   Rationale: Expected debugging queries are "recent failed runs by source" and "full or incremental runs for market prices over a range." Indexes on `(source, status, started_at)` and `(target_type, fetch_mode, range_start, range_end)` support those paths without over-indexing count or error fields.

   Alternative considered: add indexes for every column. That would add write overhead and is not tied to known Phase 1 query patterns.

## Risks / Trade-offs

- `requested_symbols` text is not convenient for SQL-level symbol filtering -> Mitigation: keep it for human/debug context and add a normalized detail table later if per-symbol queries become a real requirement.
- String statuses can drift if callers invent new values -> Mitigation: define allowed values in the model tests and documentation; defer stricter enum handling until lifecycle code exists.
- Task-level logs do not identify which individual symbol failed -> Mitigation: capture `partial` plus `error_message` now, and leave per-symbol diagnostics to a later child table if needed.
- Count semantics depend on future ingestion behavior -> Mitigation: keep counts nullable so the model can be introduced before the fetch pipeline defines every metric.

## Migration Plan

- Create an Alembic migration after the existing `market_price` migration.
- Add the `data_fetch_log` table with task scope, status, count, error, and timestamp columns.
- Add indexes for source/status/time and target/mode/range lookup paths.
- Rollback drops indexes and then the table.

## Open Questions

- None for this proposal.
