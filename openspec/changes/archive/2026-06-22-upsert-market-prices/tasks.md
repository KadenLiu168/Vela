## 1. Upsert Test Coverage

- [x] 1.1 Add tests proving a new `MarketPrice` upsert inserts one row and reports one inserted row.
- [x] 1.2 Add tests proving a repeated ETF trading date upsert updates the existing row without creating duplicates.
- [x] 1.3 Add tests proving different ETFs on the same trading date are stored independently.
- [x] 1.4 Add tests proving empty input returns zero inserted and updated rows.
- [x] 1.5 Add tests proving duplicate keys in one batch use the last supplied values and count one write.

## 2. Upsert Implementation

- [x] 2.1 Add `MarketPriceUpsertResult` and `upsert_market_prices(session, market_prices)` in the core package.
- [x] 2.2 Deduplicate input rows by `(etf_id, trade_date)` with the last row winning.
- [x] 2.3 Query existing keys before writing to calculate inserted and updated counts.
- [x] 2.4 Use SQLite `ON CONFLICT(etf_id, trade_date) DO UPDATE` to insert or update price fields.
- [x] 2.5 Export the new upsert API from `vela_core`.

## 3. Verification

- [x] 3.1 Run focused market price upsert tests.
- [x] 3.2 Run existing market price model and mapping tests.
- [x] 3.3 Run `openspec status --change "upsert-market-prices"` and confirm the change remains apply-ready.
