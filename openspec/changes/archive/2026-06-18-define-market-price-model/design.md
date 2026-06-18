## Context

Vela already has a SQLAlchemy declarative base, an `ETFInfo` ORM model, and Alembic migration discovery. The next persistence step is daily ETF market prices so market data ingestion, strategy signals, and backtests can share one durable source for historical OHLCV data.

ETF rotation strategies usually compare returns across ETFs over date ranges. Those calculations should prefer adjusted closing prices when available because distributions and splits can distort raw close-to-close returns.

## Goals / Non-Goals

**Goals:**

- Define a `MarketPrice` ORM model for ETF daily OHLCV data.
- Relate each price row to `ETFInfo`.
- Enforce one row per ETF per trading date.
- Include nullable `adjusted_close` and define the strategy price fallback rule.
- Add indexes for ETF date-range and trading-date lookups.
- Add an Alembic migration and focused schema/constraint tests.

**Non-Goals:**

- Implement market data ingestion or provider clients.
- Implement repository/query service APIs.
- Store intraday prices, live quotes, holdings, NAV, dividends, or corporate actions.
- Implement full strategy signal or backtest calculations.

## Decisions

1. Use `etf_id` as the ETF identity in `MarketPrice`.

   Rationale: `ETFInfo` already owns ETF identity by `exchange` and `symbol`. A foreign key keeps price rows tied to that identity without duplicating exchange/symbol fields or making strategy queries handle cross-exchange symbol ambiguity.

   Alternative considered: store `exchange` and `symbol` directly on every market price row. That makes standalone price rows easier to inspect, but duplicates identity data and risks drift from ETF metadata.

2. Enforce uniqueness with `(etf_id, trade_date)`.

   Rationale: daily market data has one canonical row per ETF per trading day. This unique constraint gives ingestion code a stable conflict target for future upsert behavior.

   Alternative considered: include provider or currency in the unique key. Provider-specific rows may be useful later, but Phase 1 needs one normalized daily price series for strategy and backtest use.

3. Include `adjusted_close` as nullable.

   Rationale: adjusted close is useful for return, momentum, and backtest calculations because it accounts for distributions and split-like adjustments. Keeping it nullable allows providers that only supply raw OHLCV data.

   Alternative considered: require `adjusted_close`. That would simplify strategy queries, but it would reject otherwise valid daily market data from providers that do not supply adjusted prices.

4. Define strategy price selection as `adjusted_close` first, then `close_price`.

   Rationale: strategies should use adjusted prices when available, while still being able to operate on raw close prices when adjusted data is missing.

   Alternative considered: make callers choose the price column every time. That is more flexible, but it spreads a core data-quality rule across strategy and backtest code.

5. Use decimal numeric columns for prices and integer volume.

   Rationale: SQLAlchemy `Numeric` matches the existing `ETFInfo.expense_ratio` precision style and avoids binary floating-point storage issues for price data. Volume is a whole-unit count and can be nullable for providers that omit it.

   Alternative considered: use floating-point columns for prices. That is convenient for analytics, but persisted market data should preserve decimal values as loaded.

6. Add targeted indexes for strategy queries.

   Rationale: the main expected query shape is "prices for one ETF over a date range", with some workflows also querying all ETF prices for a trading date. Indexes on `(etf_id, trade_date)` and `trade_date` support these paths and align with the unique constraint.

   Alternative considered: add separate indexes for every OHLCV column. Those are not part of known Phase 1 query patterns and would add unnecessary write overhead.

## Risks / Trade-offs

- Provider adjusted-close formulas can differ -> Treat `adjusted_close` as normalized market data for strategy use, and defer provider reconciliation until ingestion design exists.
- Nullable `adjusted_close` means strategy code needs fallback behavior -> Make the fallback rule explicit in the market-data spec.
- A single normalized row per ETF/date loses provider-level provenance -> Keep provider-specific storage out of scope until provider ingestion requirements need it.
- Composite indexes add write overhead -> Keep the index set minimal and tied to known strategy/backtest query shapes.

## Migration Plan

- Create an Alembic migration after the existing ETF metadata migration.
- Add the `market_price` table with a foreign key to `etf_info`.
- Add the `(etf_id, trade_date)` unique constraint and lookup indexes.
- Rollback drops indexes and the table.

## Open Questions

- None for this proposal.
