## 1. Tests

- [x] 1.1 Add a typical volatility unit test proving effective daily returns exclude the initial equity-curve placeholder return.
- [x] 1.2 Add a flat-return unit test that returns zero volatility.
- [x] 1.3 Add insufficient-observation unit tests that return no volatility value.

## 2. Core Implementation

- [x] 2.1 Add a frozen result dataclass for strategy volatility.
- [x] 2.2 Implement annualized volatility as population standard deviation of effective daily returns multiplied by `sqrt(252)` and quantized to six decimal places.
- [x] 2.3 Export the volatility result type and calculator from `vela_core`.

## 3. Validation

- [x] 3.1 Run the related strategy equity curve tests.
- [x] 3.2 Run full tests, lint, format check, type check, and OpenSpec validation.
