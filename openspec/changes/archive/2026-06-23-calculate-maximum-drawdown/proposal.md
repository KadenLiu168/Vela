## Why

Backtest results need a maximum drawdown metric derived from the strategy net value curve. COP-61 requires this calculation now so later backtest reporting can expose downside risk together with the existing return metrics.

## What Changes

- Add maximum drawdown calculation based on existing strategy equity curve points.
- Return the maximum drawdown value together with the peak and trough dates that define the drawdown interval.
- Return a zero drawdown with no interval for empty or non-drawing curves.
- Add focused unit tests for a typical net value curve and no-drawdown cases.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `strategy-equity-curve`: add a requirement for calculating maximum drawdown from strategy equity curve points.

## Impact

- `packages/core/src/vela_core/strategy_equity_curve.py`
- `packages/core/src/vela_core/__init__.py`
- `packages/core/tests/test_strategy_equity_curve.py`
- `openspec/specs/strategy-equity-curve/spec.md`
