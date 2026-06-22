## Context

Vela already has a full daily market data fetch command and the lower-level pieces needed for incremental fetching: active ETF metadata lookup, a date-bounded market data provider contract, AkShare date-bound support, provider-to-`MarketPrice` mapping, SQLite upsert behavior, and `DataFetchLog` fields for incremental fetch scope.

COP-36 should add the incremental path without changing the existing full fetch command behavior or introducing scheduling. The confirmed product interpretation is that "local latest trading day" means the maximum `market_price.trade_date` across the local database, not a per-ETF latest date.

## Goals / Non-Goals

**Goals:**
- Add an incremental mode to `fetch-market-data`.
- Infer the incremental request range from local market price state.
- Fetch only active ETF daily prices for the inferred date range.
- Persist through the existing upsert boundary so repeated runs do not duplicate rows.
- Record a durable `DataFetchLog` for incremental runs.

**Non-Goals:**
- Do not add a new data model or migration.
- Do not add scheduling, retry policy, background jobs, or production orchestration.
- Do not infer per-ETF incremental ranges or backfill symbol-specific gaps.
- Do not change full fetch semantics or CLI output format beyond allowing incremental mode.
- Do not automatically fall back to full fetch when no local market prices exist.

## Decisions

1. Use `fetch-market-data --incremental` as the CLI surface.

   Rationale: `fetch-market-data` is already the operator entrypoint for daily market data ingestion. A flag keeps the surface small and preserves the current default full fetch behavior.

   Alternative considered: add a separate `fetch-incremental-market-data` subcommand. That is explicit, but it duplicates command wiring and summary behavior.

2. Compute the incremental start date from the global latest local market price date.

   Rationale: COP-36 asks for incrementality based on the local latest trading day. A single global `max(market_price.trade_date) + 1 day` is simple, predictable, and easy to log as one task range.

   Alternative considered: compute one start date per ETF. That can repair symbol-specific gaps, but it complicates provider requests, log range semantics, and operator expectations beyond this ticket.

3. Keep orchestration in the core package.

   Rationale: The workflow coordinates database reads, provider calls, mapping, upsert, and logging. Keeping that logic in core matches the full fetch implementation and keeps the CLI thin.

   Alternative considered: implement incremental logic directly in `apps/cli`. That would be faster initially but would duplicate business logic and make later API or scheduler entrypoints harder.

4. Treat missing local market prices as a failed incremental run.

   Rationale: Incremental mode needs a local baseline. Automatically falling back to full fetch would make an incremental command do unexpectedly large work and obscure operator intent.

   Alternative considered: run a full fetch when no baseline exists. That is convenient, but it changes the meaning of incremental mode and can hide setup mistakes.

## Risks / Trade-offs

- Global latest date can miss older gaps for individual ETFs -> Accept for COP-36 and rely on full fetch or future gap-repair work when needed.
- Calendar-day `latest + 1 day` can land on weekends or holidays -> Provider date bounds can still return the next available trading rows, and the logged range remains the requested range.
- Provider returns no rows because local data is already current -> Record a failed no-row result using the existing workflow status rules, making no-work runs visible.
- Partial provider failures can leave some symbols stale -> Preserve existing partial behavior with failed symbols and error text in the summary and fetch log.
