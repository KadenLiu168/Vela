## Why

Backtest results need a clear annualized return metric derived from the strategy net value curve. COP-60 requires this calculation now so later backtest reporting can reuse a tested backend contract.

## What Changes

- Add annualized return calculation based on an existing strategy equity curve.
- Define the calculation口径 as start/end net value annualized over calendar-day span.
- Return no annualized value when the curve does not contain a positive elapsed day span or a positive starting net value.
- Add focused tests for complete, flat, single-point, same-day, and invalid-start cases.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `strategy-equity-curve`: add a requirement for calculating annualized return from strategy equity curve points.

## Impact

- `packages/core/src/vela_core/strategy_equity_curve.py`
- `packages/core/src/vela_core/__init__.py`
- `packages/core/tests/test_strategy_equity_curve.py`
- `openspec/specs/strategy-equity-curve/spec.md`
