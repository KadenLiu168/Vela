## 1. Tests

- [x] 1.1 Add core tests for successful full fetch logging, including scope, `success` status, fetched count, inserted count, updated count, and finish time.
- [x] 1.2 Add core tests for successful incremental fetch logging with the same result fields and `fetch_mode = "incremental"`.
- [x] 1.3 Add core tests for failed fetch logging when no requested symbol can be fetched or mapped.
- [x] 1.4 Add core tests for partial fetch logging when at least one requested symbol succeeds and at least one requested symbol fails.

## 2. Core Implementation

- [x] 2.1 Add a market data fetch orchestration module in `packages/core` with a typed public result object and a `fetch_market_prices` function.
- [x] 2.2 Create a `DataFetchLog` row with `running` status before provider calls begin.
- [x] 2.3 Resolve requested symbols to `ETFInfo` rows, call the provider per symbol, map returned `DailyPrice` values to `MarketPrice`, and upsert successful rows.
- [x] 2.4 Update the same `DataFetchLog` row with `success`, `failed`, or `partial` status, finish time, row counts, and concise error text.
- [x] 2.5 Export the orchestration API from `vela_core.__init__`.

## 3. Verification

- [x] 3.1 Run the focused market data fetch logging tests.
- [x] 3.2 Run existing market price upsert and data fetch log model tests to catch regressions.
- [x] 3.3 Run `openspec status --change "record-market-data-fetch-log"` and confirm the change is apply-ready.
