## 1. Tests

- [x] 1.1 Add focused tests for calculating 20 / 60 / 120 trading-day returns from complete `MarketPrice` history.
- [x] 1.2 Add tests for insufficient history where only available windows return values and missing windows return `None`.
- [x] 1.3 Add tests for missing `as_of_date` current price returning `None` for all windows.
- [x] 1.4 Add tests proving `adjusted_close` is used before `close_price` and other ETF histories are ignored.

## 2. Core Implementation

- [x] 2.1 Add a `MarketPriceReturns` result dataclass with `etf_id`, `as_of_date`, `return_20d`, `return_60d`, and `return_120d`.
- [x] 2.2 Implement `calculate_market_price_returns(session, *, etf_id, as_of_date)` using same-ETF `MarketPrice` rows ordered by `trade_date`.
- [x] 2.3 Calculate each window as `current strategy price / prior strategy price - 1`, returning `None` when current or prior prices are unavailable.

## 3. Public API

- [x] 3.1 Export the result type and calculation function from `vela_core.__init__`.
- [x] 3.2 Keep the implementation independent of CLI commands, database schema changes, and strategy configuration loading.

## 4. Verification

- [x] 4.1 Run `uv run pytest packages/core/tests/test_market_price_returns.py`.
- [x] 4.2 Run `openspec status --change "calculate-market-price-window-returns"` and confirm the change is apply-ready.
