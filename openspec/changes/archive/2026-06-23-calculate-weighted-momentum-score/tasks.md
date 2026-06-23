## 1. Tests

- [x] 1.1 Add a typical-input unit test that calculates short and long configured returns and verifies the weighted score.
- [x] 1.2 Add a unit test proving non-20/60/120 configured windows are used.
- [x] 1.3 Add a reproducibility unit test that repeats the same calculation and verifies identical results.
- [x] 1.4 Add missing-history and missing-current-price unit tests that return null component returns and null score.
- [x] 1.5 Add a unit test proving other ETF histories are ignored.

## 2. Core Implementation

- [x] 2.1 Add a frozen result dataclass for `etf_id`, `as_of_date`, short return, long return, and score.
- [x] 2.2 Implement a momentum scoring function that accepts a SQLAlchemy session, ETF id, as-of date, and `StrategyConfig`.
- [x] 2.3 Query only the requested ETF's prices through `as_of_date`, ordered newest first, with enough rows for the configured long window.
- [x] 2.4 Calculate component returns as `current strategy price / prior strategy price - 1` using configured trading-row windows.
- [x] 2.5 Calculate the weighted score with Decimal arithmetic and return null when either component return is unavailable.
- [x] 2.6 Export the result type and calculation function from `vela_core`.

## 3. Verification

- [x] 3.1 Run the focused momentum scoring tests.
- [x] 3.2 Run the existing market price return tests to confirm behavior was not regressed.
- [x] 3.3 Run `openspec status --change "calculate-weighted-momentum-score"` and confirm the change is apply-ready.
