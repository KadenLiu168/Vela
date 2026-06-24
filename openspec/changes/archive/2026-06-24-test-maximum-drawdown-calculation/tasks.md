## 1. Test Coverage

- [x] 1.1 Add a focused maximum drawdown test for a monotonically falling net value curve.
- [x] 1.2 Add a focused maximum drawdown test for a drawdown-then-recovery net value curve.
- [x] 1.3 Confirm existing rising-curve coverage satisfies the no-drawdown acceptance case.

## 2. Implementation Fixes

- [x] 2.1 Keep production maximum drawdown code unchanged unless the new tests expose an incorrect calculation.
- [x] 2.2 If a defect is exposed, make the smallest focused fix in maximum drawdown calculation.

## 3. Verification

- [x] 3.1 Run the focused strategy equity curve maximum drawdown tests.
- [x] 3.2 Run `uv run pytest`.
- [x] 3.3 Run lint/type checks available in project commands.
- [x] 3.4 Run OpenSpec validation for `test-maximum-drawdown-calculation`.
