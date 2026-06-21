## 1. Tests

- [x] 1.1 Add AkShare provider tests that fake the AkShare module and verify successful ETF daily OHLCV normalization into `DailyPrice`.
- [x] 1.2 Add tests for default request parameters: `period="daily"`, `adjust=""`, and `YYYYMMDD` date bounds.
- [x] 1.3 Add tests for empty AkShare results returning an empty sequence.
- [x] 1.4 Add tests for AkShare call failures and normalization failures raising a catchable provider-level error with source, symbol, and date-range context.
- [x] 1.5 Add tests confirming the existing provider contract module remains independent from AkShare and pandas imports.

## 2. Implementation

- [x] 2.1 Add `akshare` to project dependencies.
- [x] 2.2 Add a dedicated AkShare provider module under `vela_core`.
- [x] 2.3 Implement `AkShareMarketDataProvider` with provider name, AkShare `fund_etf_hist_em` calls, default unadjusted daily requests, and date formatting.
- [x] 2.4 Map AkShare `日期`, `开盘`, `最高`, `最低`, `收盘`, and `成交量` columns into sorted `DailyPrice` values using `Decimal(str(value))` for prices.
- [x] 2.5 Implement provider-level error wrapping for AkShare source errors, missing required columns, and row parsing failures.
- [x] 2.6 Export the AkShare provider and provider error type from a predictable import path.

## 3. Verification

- [x] 3.1 Run the focused market data provider tests.
- [x] 3.2 Run the full core test suite.
- [x] 3.3 Run `ruff check .`.
- [x] 3.4 Run `openspec status --change "implement-akshare-market-data-provider"` and confirm the change is ready for apply.
