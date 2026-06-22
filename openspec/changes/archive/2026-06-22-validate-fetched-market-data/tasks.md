## 1. Validation Test Coverage

- [x] 1.1 Add AkShare provider tests for missing, null, empty, and pandas null-like required row values.
- [x] 1.2 Add AkShare provider tests for invalid trade dates and invalid OHLC decimal values.
- [x] 1.3 Add AkShare provider tests for non-positive OHLC prices and inconsistent high/low relationships.
- [x] 1.4 Add AkShare provider tests for invalid, non-integral, and negative volume values.
- [x] 1.5 Add AkShare provider test proving one invalid row fails the whole result without partial `DailyPrice` output.
- [x] 1.6 Assert validation error messages include source, symbol, requested date range, row index, field or column, invalid value, and reason.

## 2. Provider Validation Implementation

- [x] 2.1 Add focused validation helpers inside `akshare_market_data_provider.py` for required values, dates, decimals, volume, and OHLC consistency.
- [x] 2.2 Call validation during `_normalize_rows` before constructing each `DailyPrice`.
- [x] 2.3 Raise `MarketDataProviderError` with actionable source row context for validation failures.
- [x] 2.4 Preserve existing successful normalization behavior, date sorting, empty-result behavior, and public provider API.

## 3. Verification

- [x] 3.1 Run AkShare provider tests and fix any regressions.
- [x] 3.2 Run the core test suite relevant to market data provider behavior.
- [x] 3.3 Run `openspec status --change "validate-fetched-market-data"` and confirm the change is apply-ready.
