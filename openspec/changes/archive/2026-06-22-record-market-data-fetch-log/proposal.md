## Why

Market data fetching already has a durable `DataFetchLog` model, but the actual fetch workflow does not yet write log rows. Without runtime fetch logs, full and incremental market data runs cannot be audited for requested scope, outcome, row counts, or provider errors.

## What Changes

- Add a core market data fetch orchestration path that records one `DataFetchLog` row for each fetch task.
- Log full and incremental fetch scope, including source, target type, fetch mode, date range, and requested symbols.
- Update the same log row with final status, fetched row count, inserted/updated counts, finish time, and error message.
- Preserve provider and upsert boundaries: providers fetch normalized prices, mapping converts rows, upsert persists prices, and orchestration owns fetch logging.

## Capabilities

### New Capabilities

### Modified Capabilities
- `market-data`: Add requirements that full and incremental market price fetch workflows write `DataFetchLog` rows with scope, status, counts, and errors.

## Impact

- Core package: adds a market data fetch orchestration module and public API.
- Database: uses the existing `data_fetch_log`, `etf_info`, and `market_price` tables; no schema migration is expected.
- Tests: adds focused core tests for successful, failed, and partial fetch logging.
