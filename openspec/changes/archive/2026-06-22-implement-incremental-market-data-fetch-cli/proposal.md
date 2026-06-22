## Why

COP-36 needs an operator-facing way to fetch only ETF daily market prices that are newer than the local database state. The full fetch command exists, but repeated full refreshes are inefficient once the local SQLite database already has historical prices.

## What Changes

- Add an incremental mode to the existing market data fetch CLI command.
- Infer the incremental date range from the latest local `market_price.trade_date`, using the next calendar day as the provider request start date.
- Fetch incremental daily prices for active ETFs through the existing market data provider contract.
- Persist incremental prices through the existing `MarketPrice` mapping and SQLite upsert path.
- Record incremental fetch runs in `DataFetchLog` with `fetch_mode = "incremental"`, requested date range, requested symbols, status, row counts, and errors.
- Keep the existing full fetch behavior unchanged when incremental mode is not requested.

## Capabilities

### New Capabilities

### Modified Capabilities
- `market-data`: Add an incremental active-ETF market price fetch workflow based on the latest local market price date.
- `cli-database-initialization`: Extend the CLI market data fetch command with an incremental mode.

## Impact

- CLI app: adds an incremental flag to `fetch-market-data`.
- Core package: adds reusable orchestration for incremental active-ETF market price fetches.
- Database: uses existing `etf_info`, `market_price`, and `data_fetch_log` tables; no schema migration is expected.
- Tests: adds focused core workflow tests and CLI argument tests.
