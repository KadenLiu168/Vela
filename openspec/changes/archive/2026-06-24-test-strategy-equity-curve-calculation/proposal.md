## Why

COP-72 needs explicit regression coverage proving strategy equity curve net value calculation stays correct for held ETF returns, initial net value, daily compounding, and rebalance effects. The equity curve API already exists, but focused tests should make the backtest net value contract harder to regress.

## What Changes

- Add focused core tests for basic held-position return calculation from stored market prices.
- Verify the initial net value, each daily net value, and daily return values across a multi-day curve.
- Verify rebalance-day holdings affect the following daily return calculation.
- Keep production equity curve behavior unchanged unless the new tests expose a defect.

## Capabilities

### New Capabilities

### Modified Capabilities
- `strategy-equity-curve`: Clarify regression coverage for initial net value, daily net values, held-position return calculation, and rebalance effects.

## Impact

- Affected code: `packages/core/src/vela_core/strategy_equity_curve.py` only if tests expose a necessary fix.
- Affected tests: `packages/core/tests/test_strategy_equity_curve.py`.
- Dependencies: no new runtime dependencies.
- Systems: Phase 1 core backend backtest confidence for historical strategy net value calculation.
