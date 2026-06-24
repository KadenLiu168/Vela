## 1. Test Coverage

- [x] 1.1 Add a focused market price upsert test for duplicate rows with the same ETF and trading date in one call.
- [x] 1.2 Assert the duplicate upsert persists exactly one `market_price` row for that ETF and trading date and keeps the last supplied values.

## 2. Implementation

- [x] 2.1 Run the focused upsert test and update `upsert_market_prices` only if the new coverage fails.

## 3. Validation

- [x] 3.1 Run the focused market price upsert tests.
- [x] 3.2 Run `uv run pytest`.
- [x] 3.3 Run OpenSpec validation for `test-market-data-upsert-deduplication`.
