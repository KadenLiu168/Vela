## Why

Backtest results already expose a `volatility` metric column, but the core backend does not yet provide a tested way to calculate it from strategy returns. COP-62 needs a clear, reusable annualized volatility calculation before later backtest summary code can persist the metric.

## What Changes

- Add a core strategy volatility calculation based on the strategy equity curve daily return sequence.
- Define the calculation basis explicitly: exclude the initial equity-curve placeholder return, calculate the standard deviation of daily returns, annualize with 252 trading days, and quantize to six decimal places.
- Return no volatility when there are fewer than two effective daily return observations.
- Cover typical, flat, and insufficient-return cases with tests.

## Capabilities

### New Capabilities

### Modified Capabilities
- `strategy-equity-curve`: Add annualized volatility calculation from strategy equity curve daily returns.

## Impact

- Affected code: `packages/core/src/vela_core/strategy_equity_curve.py`, `packages/core/src/vela_core/__init__.py`
- Affected tests: `packages/core/tests/test_strategy_equity_curve.py`
- Affected specs: `openspec/specs/strategy-equity-curve/spec.md`
- No database schema, CLI, API, or dependency changes expected.
