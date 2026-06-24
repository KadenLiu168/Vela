## Why

COP-63 needs a reusable Sharpe ratio calculation so backtest summaries can compare risk-adjusted strategy performance. The calculation depends on existing annualized return and volatility metrics plus a configured risk-free rate.

## What Changes

- Add strategy configuration support for an annual risk-free rate used by performance metrics.
- Add a strategy Sharpe ratio result type and calculator based on annualized return, annualized volatility, and risk-free rate.
- Define zero-volatility and unavailable-input behavior as returning no Sharpe ratio value.
- Cover typical, negative excess return, unavailable input, and zero-volatility scenarios with unit tests.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `strategy-configuration`: Add a required annual risk-free rate configuration for performance metrics.
- `strategy-equity-curve`: Add Sharpe ratio calculation from annualized return, volatility, and configured risk-free rate.

## Impact

- Code: `packages/core/src/vela_core/strategy_config.py`, `packages/core/src/vela_core/strategy_equity_curve.py`, and package exports.
- Config: `config/strategy_v1.yaml`.
- Tests: strategy configuration and strategy equity curve unit tests.
- OpenSpec: delta specs for `strategy-configuration` and `strategy-equity-curve`.
- No database migration is needed because `BacktestRun.sharpe_ratio` already exists and is nullable.
