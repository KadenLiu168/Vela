## Context

`strategy_equity_curve.py` already calculates the equity curve, annualized return, maximum drawdown, and annualized volatility for Phase 1 backtest metrics. `BacktestRun` already has a nullable `sharpe_ratio` column, but the core package has no Sharpe ratio helper and the checked-in strategy configuration has no risk-free rate.

COP-63 requires Sharpe ratio calculation from annualized return, volatility, and a configured risk-free rate. During Explore, the user selected adding a formal configuration field and returning no Sharpe ratio when volatility is zero.

## Goals / Non-Goals

**Goals:**

- Add `performance.risk_free_rate` to the strategy configuration schema and checked-in `strategy_v1.yaml`.
- Add a reusable Sharpe ratio calculator alongside the existing strategy equity curve metric helpers.
- Return a nullable result for unavailable annualized return, unavailable volatility, and zero volatility.
- Quantize calculated Sharpe ratios to six decimal places.

**Non-Goals:**

- Persist Sharpe ratio into `BacktestRun`.
- Add a backtest runner or summary orchestration.
- Change annualized return or volatility calculation behavior.
- Add database migrations or new dependencies.

## Decisions

1. Add `performance.risk_free_rate` as a required strategy configuration group.

   Rationale: COP-63 explicitly references risk-free return configuration. A dedicated `performance` group keeps the field separate from transaction costs and gives later backtest reporting a stable place for metric inputs.

   Alternative considered: pass `risk_free_rate` only to the helper. That would be smaller, but it would not establish the configuration contract requested by the issue.

2. Add `StrategySharpeRatio` and `calculate_strategy_sharpe_ratio(...)` to `strategy_equity_curve.py`.

   Rationale: Existing backtest metric helpers and result dataclasses already live in this module. Keeping Sharpe ratio there avoids a one-function metrics module and keeps exports consistent.

   Alternative considered: create a generic performance metrics module. That would be premature for one additional metric.

3. Return `StrategySharpeRatio(sharpe_ratio=None)` when annualized return is missing, volatility is missing, or volatility is zero.

   Rationale: The existing metric helpers use nullable values to represent unavailable calculations. Zero volatility makes the ratio undefined, and `BacktestRun.sharpe_ratio` is nullable.

   Alternative considered: return `0.000000` for zero volatility and zero excess return. That adds a special case for a mathematically undefined division without improving downstream behavior.

## Risks / Trade-offs

- Required new config group can break ad hoc test configs that omit it -> Update local test fixtures in the same change.
- `float` configuration values become `Decimal(str(...))` at calculation boundaries -> Keep six-decimal quantization and existing project style for pragmatic numeric handling.
- Sharpe ratio is not automatically persisted yet -> Leave persistence to the later backtest runner so COP-63 stays focused on the calculation contract.
