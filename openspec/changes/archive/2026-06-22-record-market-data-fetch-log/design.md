## Context

Vela already has the pieces needed to fetch and persist daily ETF market prices: a `MarketDataProvider` protocol, an AkShare provider, provider-to-ORM mapping, SQLite upsert behavior, and a `DataFetchLog` ORM model. Previous changes intentionally kept providers and upsert logic separate from fetch orchestration and log writes.

This change fills that orchestration gap. The logging behavior belongs in core package business logic because it coordinates provider calls, ETF metadata lookup, price persistence, and durable task audit state.

## Goals / Non-Goals

**Goals:**
- Record one `DataFetchLog` row for each full or incremental market price fetch task.
- Preserve the requested scope, lifecycle status, result counts, and error details for troubleshooting.
- Continue fetching remaining symbols when one symbol fails so mixed outcomes can be recorded as `partial`.
- Keep provider, mapping, and upsert modules focused on their existing responsibilities.

**Non-Goals:**
- Do not add a scheduler, retry policy, CLI command, or external job runner.
- Do not infer incremental date ranges automatically.
- Do not add per-symbol log tables or schema migrations.
- Do not move database writes into provider implementations.

## Decisions

1. Use one `DataFetchLog` row per fetch task.

   Rationale: the existing model and specs describe task-level logging with `requested_symbols`. A row per symbol would add detail but would change the audit model before a concrete need exists.

   Alternative considered: write one log row per provider request. That would simplify per-symbol diagnostics, but it would make "one full run" harder to inspect and would not match the current task-level model.

2. Add a small core orchestration API.

   Rationale: a fetch workflow needs to coordinate provider calls, ETF lookup, mapping, upsert, and log status updates. Keeping this in `packages/core` makes it testable and reusable by later CLI or scheduled entrypoints.

   Alternative considered: implement logging in a CLI command. That would satisfy one entrypoint but would duplicate behavior once other callers need market data fetches.

3. Treat provider or metadata failures per symbol and continue the task.

   Rationale: multi-symbol market data fetches commonly fail for a subset of symbols. Continuing allows successful symbols to be persisted and records a `partial` outcome with useful error details.

   Alternative considered: fail fast on the first symbol error. That is simpler, but it wastes successful fetch opportunities and makes partial market data runs less observable.

4. Count semantics follow existing boundaries.

   Rationale: `rows_fetched` should count normalized provider `DailyPrice` values, while `rows_inserted` and `rows_updated` should sum the `upsert_market_prices` result. These fields then distinguish provider output from database impact.

   Alternative considered: store only inserted and updated counts. That loses the ability to detect successful provider fetches that resulted in no database changes.

## Risks / Trade-offs

- Partial runs can leave some symbols updated and others stale -> The `partial` status and error message preserve which symbols failed for follow-up.
- Error messages can become long for many failures -> Keep messages concise by including symbol and exception text, with no stack trace in the log field.
- Unknown ETF symbols block mapping to `MarketPrice` -> Treat missing ETF metadata as a per-symbol failure and record it in the same task log.
- Caller-managed sessions can leave changes uncommitted -> Document and test behavior at the session level; transaction ownership remains with the caller.
