## Why

Vela already has ETF metadata, AkShare daily price fetching, market price mapping, SQLite upsert behavior, and fetch log storage, but there is no CLI command that runs a full market data fetch end to end. COP-35 needs a first Phase 1 command that can populate daily prices for the active ETF universe and leave an auditable execution record.

## What Changes

- Add a CLI command for full ETF daily market data fetching.
- Treat the current ETF pool as `ETFInfo` rows where `is_active = true`; do not introduce a separate named pool model.
- Fetch daily prices through the existing AkShare provider and persist them through the existing market price mapping and SQLite upsert boundary.
- Record one `DataFetchLog` row for each command run with scope, status, row counts, finish time, and error text.
- Print a clear command summary including requested symbol count, fetched row count, inserted row count, updated row count, status, and failed symbols when applicable.

## Capabilities

### New Capabilities

### Modified Capabilities
- `market-data`: Add full active-ETF market data fetch workflow behavior, including active ETF scope, persistence, fetch logging, and partial failure handling.
- `cli-database-initialization`: Extend the CLI surface with a full market data fetch command that accepts a database URL and reports execution results.

## Impact

- CLI app: adds a new market data fetch subcommand under `apps/cli`.
- Core package: adds reusable orchestration for full active-ETF market data fetches.
- Database: uses existing `etf_info`, `market_price`, and `data_fetch_log` tables; no schema migration is expected.
- Tests: adds focused core orchestration tests and CLI command tests with fake providers or monkeypatched orchestration.
