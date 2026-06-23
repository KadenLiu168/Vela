## Why

COP-59 requires backtest net value calculations to reflect transaction costs instead of reporting a frictionless equity curve. The strategy configuration already defines transaction cost parameters, so the equity curve calculation should consume them when daily holdings change.

## What Changes

- Apply transaction costs when calculating strategy equity curve daily returns.
- Derive turnover from changes in target holding weights between adjacent trading dates.
- Read `transaction_cost_bps` from the strategy configuration used for the calculation.
- Add unit tests for cost calculation on initial entry, rebalances, and zero-cost configuration.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `strategy-equity-curve`: Daily strategy net value SHALL deduct transaction costs derived from strategy configuration and holding turnover.

## Impact

- `packages/core/src/vela_core/strategy_equity_curve.py`
- `packages/core/tests/test_strategy_equity_curve.py`
- `openspec/specs/strategy-equity-curve/spec.md`
