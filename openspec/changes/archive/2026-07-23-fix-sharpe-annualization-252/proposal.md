## Why

`calculate_strategy_sharpe_ratio` computes Sharpe as `(CAGR - rf) / volatility`, but CAGR uses 365 calendar days for annualization while volatility uses √252 (trading days). The two annualization conventions are mixed in one ratio, making the Sharpe value non-standard and not directly comparable with industry results. This fix aligns Sharpe computation with the industry-standard approach: compute directly from daily excess returns × √252.

## What Changes

- **BREAKING Python API**: the package-exported `calculate_strategy_sharpe_ratio` signature changes from `(annualized_return, volatility, *, risk_free_rate)` to `(points, *, risk_free_rate)` so it can calculate Sharpe from the observed return series.
- Exclude the initial equity-curve placeholder return, subtract `risk_free_rate / 252` from each effective daily return, and calculate `mean(daily_excess_returns) / population_stddev(daily_excess_returns) × √252`, quantized to six decimal places.
- Return no Sharpe ratio when there are fewer than two effective return observations or their population standard deviation is zero.
- Backtest runner call site updated to pass `points` instead of `annualized_return` + `volatility`.
- CAGR and Volatility functions are NOT changed — each retains its semantically correct annualization convention (CAGR on 365 calendar days, Volatility on √252 trading days). The fix is at the Sharpe level only, decoupling it from these intermediate metrics.
- Existing persisted backtest rows are not recalculated; newly executed backtests use the corrected Sharpe formula.
- Sharpe ratio unit and runner integration tests are updated for the daily-returns-based contract.

## Capabilities

### New Capabilities
<!-- No new capabilities — this modifies existing behavior -->

### Modified Capabilities
- `strategy-equity-curve`: Sharpe ratio calculation changes from derived annualized metrics to effective equity-curve daily returns, using population standard deviation and 252 trading days.

## Impact

- **Code**: `packages/core/src/vela_core/strategy_equity_curve.py` (`calculate_strategy_sharpe_ratio`), `packages/core/src/vela_core/backtest_runner.py` (call site), `packages/core/src/vela_core/__init__.py` (export remains present)
- **Tests**: `packages/core/tests/test_strategy_equity_curve.py` (all Sharpe-related tests rewritten), `packages/core/tests/test_backtest_runner.py` (mock updated)
- **REST/CLI/Web contracts**: No response-field or command-output shape change; Sharpe values from newly run backtests change semantically
- **Database**: No schema or migration changes; historical `BacktestRun.sharpe_ratio` values remain as originally calculated
- **Breaking**: The public Python package export changes signature; repository search finds one production call site, which is updated in this change
