## Context

The API service already exposes local command-style endpoints backed by request-scoped SQLite sessions. The core package already provides `generate_strategy_signal`, which calculates a signal for one date and persists the signal run and positions in the same SQLAlchemy session.

COP-98 adds the frontend-facing action for signal generation. The user decision fixes the API surface as `POST /api/strategy-signals/generate` with an optional `signalDate` query parameter and no JSON body schema.

## Goals / Non-Goals

**Goals:**

- Expose `POST /api/strategy-signals/generate`.
- Accept optional `signalDate` as a query parameter in `YYYY-MM-DD` format.
- Infer the latest local market trading date from `MarketPrice.trade_date` when `signalDate` is omitted.
- Reuse existing config loading and `generate_strategy_signal` behavior.
- Return the generated signal fields and positions needed by the frontend.
- Validate the route with FastAPI, a temporary SQLite database, and the real core generation workflow.

**Non-Goals:**

- Do not add a JSON request body schema.
- Do not change signal generation algorithms.
- Do not add new database tables, columns, migrations, or dependencies.
- Do not implement frontend UI calls in this COP.

## Decisions

1. Use `POST /api/strategy-signals/generate?signalDate=YYYY-MM-DD`.
   - Rationale: signal generation mutates local SQLite state, and the path names the persisted domain resource precisely.
   - Alternative considered: `POST /api/signals/generate`, which is shorter but less explicit.
   - Alternative considered: JSON body input, which is unnecessary for one optional field and does not match the existing simple API style.

2. Resolve omitted `signalDate` from the maximum local `MarketPrice.trade_date`.
   - Rationale: this matches the existing CLI default and the issue requirement for "latest local market trading date".
   - Alternative considered: deriving a date from the current calendar day, which could generate against unavailable local data.

3. Keep business behavior in `vela_core`.
   - Rationale: the API route should load config, resolve input, call `generate_strategy_signal`, and serialize the result without duplicating strategy logic.
   - Alternative considered: API-local scoring or persistence logic, which would violate the existing service boundary.

## Risks / Trade-offs

- Empty local market data prevents default date inference -> Return a clear API error before running signal generation.
- `signalDate` format errors rely on FastAPI date parsing -> Use the typed query parameter so invalid values fail before generation.
- Integration test data must satisfy the strategy windows -> Reuse the existing core test pattern with enough deterministic SQLite market price history.
