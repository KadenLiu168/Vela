## 1. Mapping Tests

- [x] 1.1 Add a focused test that maps a `DailyPrice` plus `etf_id` into a `MarketPrice` row and asserts every mapped field value.
- [x] 1.2 Add type assertions for mapped `trade_date`, decimal price fields, optional `adjusted_close`, and optional integer `volume`.
- [x] 1.3 Add an integration-style unit test that normalizes Fake AkShare ETF daily rows into `DailyPrice` and then maps the result into `MarketPrice`.

## 2. Core Implementation

- [x] 2.1 Add a small core mapping function that accepts `DailyPrice` and keyword-only `etf_id`.
- [x] 2.2 Construct `MarketPrice` with only the caller-provided `etf_id` and provider daily price fields.
- [x] 2.3 Export the mapper from the core package if tests or downstream code need the public import path.

## 3. Verification

- [x] 3.1 Run the new mapping tests and existing AkShare provider tests.
- [x] 3.2 Run the relevant core test subset to confirm existing market data model behavior still passes.
