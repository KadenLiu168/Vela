## Context

The FastAPI app currently exposes `/api/health` and `/api/config`. The Dashboard page introduced by earlier frontend work has no single backend read model for first-screen workflow state.

The persisted data needed by COP-86 already exists in core SQLAlchemy models: `MarketPrice`, `StrategySignal`, `StrategySignalPosition`, and `BacktestRun`. API database wiring also already exists through the request-scoped session dependency.

## Goals / Non-Goals

**Goals:**
- Return strategy summary, market data status, latest signal summary, and recent backtest summary from one local API request.
- Keep dashboard aggregation read-only and backed by real SQLite queries.
- Put aggregation logic in `vela_core` so API routes stay thin.
- Cover the integration path with a real SQLite database, ORM rows, and FastAPI `TestClient`.

**Non-Goals:**
- Do not generate signals or run backtests from the dashboard endpoint.
- Do not add new database tables or migrations.
- Do not implement frontend dashboard rendering in this COP.
- Do not introduce pagination, filtering, or configurable dashboard widgets.

## Decisions

1. Add a core dashboard aggregation service.
   - Rationale: API routes should wrap core capabilities rather than duplicate strategy, signal, market data, or backtest logic.
   - Alternative considered: build the response directly in `vela_api.main`. Rejected because it would make the API entrypoint own business query behavior.

2. Use a compact dictionary-compatible read model with dataclasses at the core boundary.
   - Rationale: Existing core report helpers use simple dataclasses and API endpoints already return plain JSON-compatible objects.
   - Alternative considered: add Pydantic response models. Rejected for this narrow read endpoint because FastAPI can serialize dictionaries and the project does not yet use response schemas in `apps/api`.

3. Derive market data status from `MarketPrice` SQLite aggregates.
   - Rationale: COP-86 explicitly requires real market price aggregation. The useful first-screen fields are total price rows, covered ETF count, earliest trade date, and latest trade date.
   - Alternative considered: infer coverage from configured ETF pool or fetch logs. Rejected because those do not prove local price rows exist.

4. Use latest persisted rows for signal and backtest summaries.
   - Rationale: The Dashboard needs current workflow state, not a historical list. Querying the newest signal and newest backtest by timestamp/date/id matches the existing persistence contracts without adding filters.
   - Alternative considered: expose full lists. Rejected as broader than the first-screen aggregate requirement.

## Risks / Trade-offs

- Empty local database can produce null summaries -> return explicit counts and `null` latest/recent objects so the frontend can distinguish "no data yet" from API failure.
- "Latest" ordering can be ambiguous when timestamps match -> include id as a deterministic tie-breaker.
- Dataclass-to-dict serialization can accidentally leak non-JSON types -> convert dates, datetimes, and decimals to strings at the core boundary.
