## Why

Market data ingestion can receive repeated rows for the same ETF and trading date from provider output or retry paths. COP-68 needs explicit regression coverage proving the existing market price upsert boundary deduplicates those rows instead of creating duplicate `market_price` records.

## What Changes

- Add focused test coverage for duplicate ETF/trading-date market price writes.
- Verify upsert keeps one database row for a repeated ETF/trading-date key and stores the last supplied values.
- Leave production implementation unchanged unless the new tests expose a defect.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `market-data`: Clarify test-covered SQLite upsert behavior for duplicate ETF/trading-date market price rows.

## Impact

- Affected tests: `packages/core/tests/test_market_price_upsert.py`.
- Affected implementation: `packages/core/src/vela_core/market_price_upsert.py` only if existing behavior fails the new coverage.
- No API, schema, dependency, or CLI changes expected.
