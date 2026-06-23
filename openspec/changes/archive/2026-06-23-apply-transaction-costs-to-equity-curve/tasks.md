## 1. Core Calculation

- [x] 1.1 Update strategy equity curve calculation to accept strategy configuration and read `transaction_cost_bps`.
- [x] 1.2 Calculate target-weight turnover between adjacent holding snapshots and deduct transaction costs from daily returns.

## 2. Tests

- [x] 2.1 Add unit tests for initial entry cost, rebalance cost, and zero transaction cost behavior.
- [x] 2.2 Update existing strategy equity curve tests to use the strategy configuration contract.

## 3. Validation

- [x] 3.1 Run focused strategy equity curve tests.
- [x] 3.2 Run project test, lint, format check, type check, and OpenSpec validation commands.
