## Why

COP-73 needs explicit regression coverage proving maximum drawdown calculation is correct across common strategy net value curves. The calculation helper already exists, but the tests should directly cover rising, falling, and recovery-after-drawdown cases so backtest downside-risk reporting is harder to regress.

## What Changes

- Add focused core tests for maximum drawdown on monotonically rising, monotonically falling, and drawdown-then-recovery net value curves.
- Verify the maximum drawdown value and peak/trough dates for loss-producing curves.
- Keep production maximum drawdown behavior unchanged unless the new tests expose a defect.

## Capabilities

### New Capabilities

### Modified Capabilities
- `strategy-equity-curve`: Clarify regression coverage for maximum drawdown calculation across rising, falling, and recovery net value curves.

## Impact

- Affected code: `packages/core/src/vela_core/strategy_equity_curve.py` only if tests expose a necessary fix.
- Affected tests: `packages/core/tests/test_strategy_equity_curve.py`.
- Dependencies: no new runtime dependencies.
- Systems: Phase 1 core backend backtest metric confidence for maximum drawdown.
