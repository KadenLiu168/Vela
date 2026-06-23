## Why

ETF rotation signals need a tested MA120 input so strategy code can filter holdings by longer-term trend. Vela already stores normalized daily market prices and has window-return calculations, but it does not yet expose a reusable 120-trading-day moving average.

## What Changes

- Add a core calculation for a single ETF's 120-trading-day moving average as of a requested date.
- Use the existing strategy price rule: `adjusted_close` when present, otherwise `close_price`.
- Return `None` for the MA120 value when the current price row is missing or fewer than 120 same-ETF price rows are available.
- Add focused test coverage for complete history, insufficient history, missing current price, adjusted-close selection, and ETF isolation.
- Do not add strategy signal generation integration, database fields, market data ingestion changes, or trend decision rules.

## Capabilities

### New Capabilities

### Modified Capabilities
- `market-data`: Add requirements for calculating a 120-trading-day moving average from stored `MarketPrice` history.

## Impact

- Adds a small core API in `packages/core` for MA120 calculation.
- Exports the new result dataclass and calculation function from `vela_core`.
- Updates market-data specification coverage and adds unit tests.
- No database migration or dependency changes.
