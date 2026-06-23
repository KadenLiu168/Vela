## 1. Tests

- [x] 1.1 Add tests for calculating MA120 from exactly 120 same-ETF `MarketPrice` rows through `as_of_date`.
- [x] 1.2 Add tests returning `ma_120d=None` when history has fewer than 120 same-ETF rows.
- [x] 1.3 Add tests returning `ma_120d=None` when the requested `as_of_date` price row is missing.
- [x] 1.4 Add tests proving `adjusted_close` is used before `close_price` and other ETF histories are ignored.

## 2. Core Implementation

- [x] 2.1 Add a `MarketPriceMovingAverage` result dataclass with `etf_id`, `as_of_date`, and `ma_120d`.
- [x] 2.2 Implement `calculate_market_price_moving_average(session, *, etf_id, as_of_date)` using the current row plus 119 prior same-ETF rows ordered by `trade_date`.
- [x] 2.3 Export the new dataclass and calculation function from `vela_core`.

## 3. Verification

- [x] 3.1 Run the focused moving-average tests.
- [x] 3.2 Run related market price return tests to confirm the adjacent calculation API still passes.
