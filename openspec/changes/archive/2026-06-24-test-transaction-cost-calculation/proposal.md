## Why

COP-74 requires regression coverage for transaction cost calculation in strategy equity curves. Existing tests cover basic entry, rebalance, and zero-cost cases, but they do not explicitly exercise multiple turnover magnitudes and cost rates together with the resulting net value impact.

## What Changes

- Add focused strategy equity curve tests for transaction costs across different turnover amounts.
- Add focused strategy equity curve tests for different configured transaction cost rates.
- Verify that transaction cost deductions reduce daily return and compound into net value as expected.
- Do not change production calculation logic unless the new tests expose a defect.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `strategy-equity-curve`: Adds explicit regression-test requirements for transaction cost calculation across turnover, cost-rate, and net-value impact scenarios.

## Impact

- Affected tests: `packages/core/tests/test_strategy_equity_curve.py`
- Affected specs: `openspec/specs/strategy-equity-curve/spec.md`
- No public API, database schema, CLI, dependency, or configuration changes expected.
