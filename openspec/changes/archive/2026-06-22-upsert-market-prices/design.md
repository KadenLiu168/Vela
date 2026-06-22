## Context

Vela already has a `MarketPrice` SQLAlchemy ORM model with a unique constraint on `(etf_id, trade_date)` and a mapper from provider `DailyPrice` values into `MarketPrice` rows. The missing piece is a persistence boundary that can safely write repeated or corrected daily market prices into SQLite.

## Goals / Non-Goals

**Goals:**

- Provide a small core helper for SQLite market price upserts.
- Preserve one row per ETF and trading date.
- Update existing price fields when corrected data is supplied.
- Return exact inserted and updated counts for future fetch logging.
- Leave transaction commit and rollback control to the caller.

**Non-Goals:**

- Do not add a cross-database upsert abstraction.
- Do not perform ETF lookup or provider `DailyPrice` mapping inside the upsert helper.
- Do not add schema migrations.
- Do not implement fetch orchestration or `DataFetchLog` updates.

## Decisions

1. Accept `Sequence[MarketPrice]` as the API input.

   Rationale: mapping is already handled by `to_market_price`, and keeping persistence separate avoids mixing provider normalization, ETF lookup, and database write behavior.

   Alternative considered: accept `DailyPrice` plus `etf_id`. That is convenient for callers but makes the helper responsible for mapping.

2. Use SQLite `insert(...).on_conflict_do_update(...)`.

   Rationale: the project targets SQLite for the current local workflow, and the existing unique constraint provides a precise conflict target.

   Alternative considered: query existing rows and manually insert or update ORM instances. That is more portable but adds more SQL and a weaker single-statement write path.

3. Query existing `(etf_id, trade_date)` keys before upsert to calculate counts.

   Rationale: SQLite affected row counts do not distinguish inserts from updates in the way ingestion logging needs.

   Alternative considered: return only total affected rows. That would be simpler but less useful for future `DataFetchLog.rows_inserted` and `rows_updated`.

4. Deduplicate duplicate keys in one input batch with the last value winning.

   Rationale: SQLite cannot safely update the same conflict target multiple times in one bulk statement across all dialect behaviors, and last-value-wins is simple and deterministic.

## Risks / Trade-offs

- SQLite-specific implementation limits portability -> Keep the helper explicit and avoid presenting it as a generic database upsert abstraction.
- Pre-querying keys adds one read before the write -> Accept the overhead because Phase 1 prioritizes correctness and useful counts over throughput.
- Last-value-wins can hide duplicate input rows -> Cover this behavior with a test so callers know the deterministic outcome.
