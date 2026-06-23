## Why

ETF rotation signals need comparable momentum inputs derived from stored daily prices. Vela already persists normalized `MarketPrice` history, but it does not yet provide a tested core calculation for the 20 / 60 / 120 trading-day returns needed by strategy generation.

## What Changes

- Add a core market price return calculation API for one ETF at a specified `as_of_date`.
- Calculate 20 / 60 / 120 trading-day returns from `MarketPrice` history using `MarketPrice.strategy_price`.
- Define missing-data behavior explicitly: unavailable current or historical prices produce `None` for the affected return windows.
- Add focused test coverage for complete history, insufficient history, missing current price, adjusted-close selection, and ETF isolation.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `market-data`: Add requirements for calculating 20 / 60 / 120 trading-day returns from stored `MarketPrice` history.

## Impact

- Core package: add a small calculation module and public exports.
- Tests: add focused unit tests for the return calculation behavior.
- Database schema: no changes.
- External dependencies: no changes.
