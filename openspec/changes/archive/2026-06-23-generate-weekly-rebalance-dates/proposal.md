## Why

Historical backtesting needs a deterministic weekly rebalance calendar derived from available trading dates. Defining this now gives later backtest execution a clear contract for holidays and missing trading days.

## What Changes

- Add a core backend capability that generates weekly rebalance dates from an input trading-date sequence.
- Define each weekly rebalance date as the last available trading date within an ISO week.
- Treat holidays or missing trading days by using only dates present in the input sequence, without filling or inferring calendar dates.
- Return at most one rebalance date per ISO week, sorted ascending and deduplicated.

## Capabilities

### New Capabilities

- `weekly-rebalance-dates`: Generate deterministic weekly rebalance dates from a trading-date sequence.

### Modified Capabilities

- None.

## Impact

- Adds a small pure function in `packages/core/src/vela_core`.
- Adds focused unit tests in `packages/core/tests`.
- No database, CLI, configuration, or dependency changes.
