## 1. Regression Tests

- [x] 1.1 Rewrite the positive Sharpe test in `packages/core/tests/test_strategy_equity_curve.py` to use `StrategyEquityCurvePoint` values and assert a hand-derived, hard-coded six-decimal result from:
  - observations from `points[1:]`, with a fixture that would fail if the initial placeholder were included
  - configured `risk_free_rate / 252`
  - population, not sample, standard deviation
  - `mean(daily_excess) / population_stddev(daily_excess) * √252`
- [x] 1.2 Rewrite the negative-excess-return test with at least two non-constant effective returns and assert a negative Sharpe value.
- [x] 1.3 Replace the unavailable-input tests with boundary coverage for zero effective observations and exactly one effective observation; both return `StrategySharpeRatio(sharpe_ratio=None)`.
- [x] 1.4 Keep one zero-dispersion test using at least two equal effective daily returns and assert `StrategySharpeRatio(sharpe_ratio=None)`.
- [x] 1.5 Update `packages/core/tests/test_backtest_runner.py` so the Sharpe fake uses `(points, *, risk_free_rate)` and verifies the runner passes the calculated equity-curve points plus the configured annual risk-free rate.

## 2. Core Implementation

- [x] 2.1 Rewrite `calculate_strategy_sharpe_ratio` in `packages/core/src/vela_core/strategy_equity_curve.py`:
  - Change signature from `(annualized_return: StrategyAnnualizedReturn, volatility: StrategyVolatility, *, risk_free_rate: Decimal)` to `(points: list[StrategyEquityCurvePoint], *, risk_free_rate: Decimal)`
  - Extract effective daily return observations from `points[1:]`
  - Return `None` for fewer than two effective observations
  - Compute `daily_rf = risk_free_rate / Decimal("252")` and each `daily_excess = daily_return - daily_rf`
  - Compute the population mean, variance, and standard deviation over effective daily excess returns
  - Return `None` when the population standard deviation is zero
  - Return `mean(daily_excess) / population_stddev(daily_excess) * √252`, quantized to six decimal places
- [x] 2.2 Update `packages/core/src/vela_core/backtest_runner.py` to call `calculate_strategy_sharpe_ratio(points, risk_free_rate=...)` while leaving CAGR, volatility, persistence, and result mapping behavior unchanged.
- [x] 2.3 Keep `StrategySharpeRatio` and `calculate_strategy_sharpe_ratio` exported from `vela_core`; do not change REST, CLI, Web, database, or configuration schemas.

## 3. Validation

- [x] 3.1 Run `uv run pytest packages/core/tests/test_strategy_equity_curve.py` — all Sharpe tests pass
- [x] 3.2 Run `uv run pytest packages/core/tests/test_backtest_runner.py` — all backtest runner tests pass
- [x] 3.3 Run `uv run pytest` — the current full Python suite passes; do not hard-code a stale test count
- [x] 3.4 Run `uv run --no-sync ruff check .` — no lint issues
- [x] 3.5 Run `uv run --no-sync mypy --config-file pyproject.toml` — no type errors
- [x] 3.6 Run `openspec validate fix-sharpe-annualization-252 --type change --strict` — the target Change passes strict validation
