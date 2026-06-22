## Why

Market data can be fetched repeatedly or corrected after an earlier ingestion. Vela needs a durable SQLite upsert path that preserves one daily market price row per ETF and trading date while allowing existing rows to be updated.

## What Changes

- Add a core market price upsert API that accepts mapped `MarketPrice` rows.
- Write market prices to SQLite using `(etf_id, trade_date)` as the conflict target.
- Update existing market price rows when corrected data arrives instead of inserting duplicates.
- Return inserted and updated row counts for ingestion logging.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `market-data`: Add SQLite upsert behavior for daily ETF market prices.

## Impact

- Affected code: core market data persistence module and package exports.
- Affected tests: focused market price upsert tests plus existing market price model and mapping tests.
- Public APIs: new core helper and result type for market price upserts.
- Database/schema: no migration; existing `market_price` unique constraint is used as the conflict target.
