## 1. Core Implementation

- [x] 1.1 Add typed portfolio holding result objects and a core calculation helper.
- [x] 1.2 Query latest successful strategy signals by config version and requested trading-date range.
- [x] 1.3 Carry target holdings forward across requested trading dates and expose the helper from `vela_core`.

## 2. Tests and Validation

- [x] 2.1 Add core tests for daily holdings, interval carry-forward, rebalance boundaries, reruns, and failed signals.
- [x] 2.2 Run focused tests, full tests, lint, type check, and OpenSpec validation.
