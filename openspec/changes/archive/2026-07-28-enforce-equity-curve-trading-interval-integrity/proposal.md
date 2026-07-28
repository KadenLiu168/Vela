## Why

Backtests currently derive their date axis from the union of stored prices, warn and continue across systematic or per-ETF gaps, and silently carry a held ETF's value when an interval endpoint price is absent. The resulting `daily_return` can represent an incomplete or multi-session interval while volatility and Sharpe still treat it as one complete trading-day observation, silently corrupting signals, equity, and performance metrics.

## What Changes

- **BREAKING**: Require official sessions in `TradingCalendar` for the requested range plus the exact preceding lookback count, and use the requested-range sessions as the authoritative backtest trading-date axis instead of the union of stored market-price dates.
- Filter the strategy's active ETF universe and per-ETF strategy history by declared inception date at each signal date so a not-yet-listed ETF or a stored pre-inception row cannot affect selection or receive an allocation.
- **BREAKING**: Fail before signal or backtest-result persistence when any official trading day is missing prices needed by the configured strategy's active ETF universe over the calculation range, including required lookback history.
- **BREAKING**: Fail equity-curve calculation when a currently held ETF lacks either endpoint price for an official trading interval; remove silent value carry/zero-return behavior.
- **BREAKING**: Remove the tolerant `BacktestGapDetectionConfig`/`gap_detection` Python API and the CLI strictness/threshold flags because required input gaps are no longer configurable or tolerable.
- Do not infer suspensions and do not forward-fill, synthesize, or silently skip missing prices.
- Report actionable missing ETF/date/interval context in failures while preserving caller-owned transaction behavior.
- Keep fetch-time gap detection warn-only; this Change tightens backtest consumption, not ingestion status.
- Preserve existing behavior for complete datasets, including T+1 effectiveness, portfolio drift, transaction costs, metric formulas, public result schemas, and existing persisted runs.

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `backtest-execution`: Make the trading calendar authoritative and require fail-fast price completeness before any backtest writes.
- `strategy-equity-curve`: Replace missing-price value carry with explicit failure for held-position interval inputs.

## Impact

- Affected code and tests: `backtest_runner.py`, strategy price-panel validation, `strategy_equity_curve.py`, the CLI gap options, public exports, and their focused tests.
- Behavioral compatibility: backtests that previously continued with warnings or frozen held values will fail without persisting partial backtest artifacts.
- Data requirements: the trading calendar must contain at least one official session in the requested range and the exact preceding lookback count, and strategy inputs must be complete for each configured active ETF from its declared inception onward.
- Unchanged systems: market-data fetch status/warnings, REST response and database schemas, historical persisted runs, and metric annualization formulas.
