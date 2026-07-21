## Why

The strategy equity curve currently applies a holding snapshot that becomes effective on date `i` to the close-to-close return interval ending on date `i`. This advances every rebalance by one return interval, reintroduces look-ahead bias despite the portfolio layer's T+1 signal handling, and can materially overstate rotation-strategy returns and risk metrics.

## What Changes

- Define each equity-curve return interval `[trading_dates[i-1], trading_dates[i]]` as earning market returns with `holding_snapshots[i-1]`.
- Continue charging date `i` transaction costs from the turnover between `holding_snapshots[i-1]` and `holding_snapshots[i]`, so entry and rebalance costs remain aligned with the newly effective target holdings.
- Correct the equity-curve specification language that currently assigns an interval-ending return to the newer snapshot.
- Replace regression expectations that preserve the look-ahead result, and add explicit coverage proving both sides of a rebalance boundary: the old holdings earn the interval ending on the rebalance-effective date, while the new holdings earn the following interval.
- Document that historical backtest results produced by the biased calculation are not comparable with corrected reruns. This Change does not mutate, label, or automatically regenerate persisted results.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `strategy-equity-curve`: Align close-to-close return attribution, transaction-cost timing, and regression coverage with T+1-effective portfolio holding snapshots.

## Impact

- Affected implementation: `packages/core/src/vela_core/strategy_equity_curve.py`.
- Affected tests: `packages/core/tests/test_strategy_equity_curve.py`, including rebalance-return and transaction-cost fixtures.
- Affected specification: `openspec/specs/strategy-equity-curve/spec.md`.
- New and manually rerun backtests may produce different equity curves and derived metrics. Existing persisted runs remain immutable and indistinguishable in the current API; result versioning, stale marking, and bulk regeneration are outside this Change and require separately approved operational scope.
- Public Python function signatures, API response shapes, CLI interfaces, and portfolio-holdings behavior remain unchanged.
