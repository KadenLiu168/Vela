## 1. Trend Filter Test Coverage

- [x] 1.1 Add a focused unit test where one ETF passes the trend filter and another ETF fails for the same `as_of_date`.
- [x] 1.2 Confirm equality, below-average price, missing current price, and missing moving average remain covered as failing boundary behavior.

## 2. Verification

- [x] 2.1 Run the focused trend filter tests.
- [x] 2.2 Run `uv run pytest`.
- [x] 2.3 Run the OpenSpec validation command for `test-trend-filter-logic`.
