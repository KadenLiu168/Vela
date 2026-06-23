## Why

ETF rotation signal generation needs a deterministic trend gate before candidates are ranked by momentum. Vela already calculates 120-trading-day moving averages, but it does not yet apply the configured price-versus-moving-average rule to exclude ETFs that are not in an uptrend.

## What Changes

- Add strategy configuration fields for the v1 trend filter: a 120-trading-day moving-average window and an `above` price relation.
- Add a core trend filter calculation for one ETF at an `as_of_date`.
- Use `MarketPrice.strategy_price` as the current price and compare it with the ETF's 120-day moving average.
- Return diagnostic values for current price, moving average, and whether the ETF passes the trend filter.
- Treat missing current price, missing moving average, and `current_price <= moving_average` as failed trend filters.
- Add focused unit tests for passing, failing, missing-data, and ETF-history-isolation scenarios.

## Capabilities

### New Capabilities
- `trend-filtering`: Applies the configured ETF trend filter using current strategy price and 120-day moving average.

### Modified Capabilities
- `strategy-configuration`: Adds the v1 trend filter configuration contract.

## Impact

- Affected code: `packages/core/src/vela_core/` strategy configuration and trend filtering module.
- Affected config: `config/strategy_v1.yaml`.
- Affected tests: strategy configuration tests and new focused trend filtering tests.
- Dependencies: no new runtime dependencies.
