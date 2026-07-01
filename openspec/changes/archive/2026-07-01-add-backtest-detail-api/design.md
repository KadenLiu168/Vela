## Context

The API already supports running a backtest and listing recent backtest runs. Core persistence already includes `BacktestRun`, `BacktestEquityCurve`, and `get_backtest_result(session, run_id=...)`, which loads a run with its equity curve ordered by trade date and row id.

## Goals / Non-Goals

**Goals:**

- Add a read-only FastAPI endpoint for one persisted backtest run.
- Shape a stable JSON response with run metadata, metrics, and equity curve points.
- Validate against real SQLite rows rather than mocked service output.

**Non-Goals:**

- No frontend detail page work.
- No dashboard aggregation or summary changes.
- No schema migration or ORM model change.
- No new backtest execution behavior.

## Decisions

- Use `GET /api/backtests/{run_id}` to align with the existing `GET /api/backtests` collection route.
- Use the existing `get_backtest_result()` core helper instead of duplicating relationship loading logic in the API route.
- Keep decimal and timestamp formatting consistent with existing backtest list/run responses: decimals are strings or null, dates/timestamps are ISO strings without timezone suffix.
- Return `404` with `{"detail": "Backtest run not found"}` for a missing run id so clients have a stable not-found response.

## Risks / Trade-offs

- Path conflict with `/api/backtests/run` → FastAPI route order already declares `/api/backtests/run` before any proposed dynamic route, and tests cover the detail path separately.
- Large equity curves may produce large responses → acceptable for Phase 1 local API usage; pagination is out of scope for COP-106.
