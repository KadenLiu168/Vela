## Context

The FastAPI service already exposes `POST /api/backtests/run` for executing and persisting a new backtest. The persisted `BacktestRun` model contains the list fields needed by COP-105: run id, date range, lifecycle status, timestamps, and metric columns. Dashboard aggregation also already reads the most recent backtest, but that aggregate intentionally returns only one summary.

## Goals / Non-Goals

**Goals:**
- Expose a read-only recent backtest run list from real `BacktestRun` rows.
- Keep the API contract small and stable for Dashboard/result entry usage.
- Support only a simple `limit` query parameter.
- Validate the endpoint with real SQLite ORM rows.

**Non-Goals:**
- Run detail API.
- Equity curve or position payloads.
- Complex filters, pagination cursors, sorting options, or search.
- Frontend wiring or Dashboard backfill behavior.

## Decisions

1. Use `GET /api/backtests` for the collection read.
   - Rationale: The existing command endpoint is nested under the same collection root at `/api/backtests/run`, so the collection path is the smallest addition.
   - Alternative considered: `GET /api/backtest-runs`. Rejected because it introduces a second naming convention for the same resource family.

2. Order recent runs by `started_at DESC, id DESC`.
   - Rationale: Existing dashboard aggregation uses the same recency definition for the latest backtest summary, and the `BacktestRun` table has an index involving `started_at`.
   - Alternative considered: order by `created_at`. Rejected because acceptance criteria specifically calls out start/end execution timing.

3. Return metric fields directly on each item.
   - Rationale: The current API style returns simple dictionaries without Pydantic response models, and existing run/dashboard responses expose metrics as stringified decimals.
   - Alternative considered: nest metrics under a `metrics` object. Rejected to keep the list item consistent with existing backtest response shapes.

4. Constrain `limit` with FastAPI query validation.
   - Rationale: A bounded positive integer is enough for Phase 1 and avoids manual validation code.
   - Alternative considered: unbounded limit. Rejected because list endpoints should not accidentally return all historical runs.

## Risks / Trade-offs

- API formatting drift from existing responses -> Reuse the existing decimal formatting helper and ISO timestamp convention from dashboard aggregation.
- Future detail API may need richer schemas -> Keep this endpoint list-only so COP-106 can define detail behavior separately.
