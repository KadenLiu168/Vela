## 1. Test Coverage

- [x] 1.1 Add an acceptance-focused strategy equity curve test covering initial net value, daily net values, weighted held-position returns, and rebalance impact.
- [x] 1.2 Keep the test data deterministic with simple stored prices, persisted successful signals, and exact `Decimal` expected values.

## 2. Implementation Fixes

- [x] 2.1 Keep production strategy equity curve code unchanged unless the new tests expose an incorrect calculation.
- [x] 2.2 If a defect is exposed, make the smallest focused fix in strategy equity curve calculation.

## 3. Verification

- [x] 3.1 Run the focused strategy equity curve tests.
- [x] 3.2 Run `uv run pytest`.
- [x] 3.3 Run the relevant OpenSpec validation command for `test-strategy-equity-curve-calculation`.
