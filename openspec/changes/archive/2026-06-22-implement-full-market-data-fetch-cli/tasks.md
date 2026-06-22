## 1. Core Tests

- [x] 1.1 Add core tests that a full fetch selects only `ETFInfo.is_active = true` rows.
- [x] 1.2 Add core tests that fetched provider `DailyPrice` rows are mapped and upserted into `market_price`.
- [x] 1.3 Add core tests for successful full fetch logging with requested symbols, `success` status, row counts, and finish time.
- [x] 1.4 Add core tests for failed full fetch logging when no active ETFs exist or no requested ETF succeeds.
- [x] 1.5 Add core tests for partial full fetch logging when at least one active ETF succeeds and another fails.

## 2. Core Implementation

- [x] 2.1 Add a reusable market data fetch orchestration module in `packages/core`.
- [x] 2.2 Define a typed full fetch result object containing status, requested symbol count, row counts, failed symbols, and error text.
- [x] 2.3 Implement active ETF lookup from `ETFInfo.is_active = true`.
- [x] 2.4 Implement full fetch orchestration using the existing provider, `to_market_price`, and `upsert_market_prices`.
- [x] 2.5 Create and update one `DataFetchLog` row per full fetch run.
- [x] 2.6 Export the orchestration API from `vela_core`.

## 3. CLI Tests

- [x] 3.1 Add CLI tests that the full fetch command accepts `--database-url` and calls the core workflow.
- [x] 3.2 Add CLI tests that omitting `--database-url` uses the existing local SQLite default.
- [x] 3.3 Add CLI tests for success, partial, and failed command summaries and exit codes.

## 4. CLI Implementation

- [x] 4.1 Add a full market data fetch subcommand to `apps/cli`.
- [x] 4.2 Wire the command to create a SQLAlchemy engine/session and call the core full fetch workflow with `AkShareMarketDataProvider`.
- [x] 4.3 Print a concise summary containing status, requested symbol count, fetched rows, inserted rows, updated rows, and failed symbols when present.
- [x] 4.4 Return zero for `success` and `partial`, and non-zero for `failed`.

## 5. Verification

- [x] 5.1 Run focused core market data fetch workflow tests.
- [x] 5.2 Run CLI tests.
- [x] 5.3 Run existing market price upsert, data fetch log model, and init-db CLI tests.
- [x] 5.4 Run `openspec status --change "implement-full-market-data-fetch-cli"` and confirm the change is apply-ready.
