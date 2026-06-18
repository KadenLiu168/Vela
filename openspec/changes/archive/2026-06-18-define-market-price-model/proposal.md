## Why

Vela needs durable daily ETF market price storage before strategy signals and backtests can query historical prices consistently. The model should establish the daily price identity, adjusted-price behavior, and indexes needed by ETF rotation workflows.

## What Changes

- Add a SQLAlchemy `MarketPrice` ORM model for ETF daily OHLCV market data.
- Store prices by ETF and trading date, with `adjusted_close` included as nullable data.
- Enforce uniqueness on `(etf_id, trade_date)` so ingestion can safely de-duplicate and upsert daily rows.
- Define lookup indexes for ETF/date-range queries and trade-date queries used by strategy calculations.
- Define strategy price selection behavior: use `adjusted_close` when present, otherwise fall back to `close_price`.

## Capabilities

### New Capabilities

### Modified Capabilities

- `market-data`: Add ETF daily market price persistence, identity, indexing, and adjusted-close fallback requirements.

## Impact

- Code: `packages/core/src/vela_core/models/`, Alembic migrations, and core model tests.
- Database: adds a new `market_price` table referencing `etf_info`.
- APIs: no public API or repository layer changes in this proposal.
- Dependencies: no new runtime dependencies.
