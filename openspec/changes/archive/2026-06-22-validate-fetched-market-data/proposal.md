## Why

AkShare market data is an external source, so malformed rows, invalid dates, bad prices, or unexpected nulls can enter Vela before database ingestion exists. The provider should fail loudly during normalization so invalid行情 is not silently treated as valid internal `DailyPrice` data.

## What Changes

- Strengthen AkShare daily price normalization with strict row-level validation for required fields, dates, OHLC prices, volume, and OHLC consistency.
- Make any invalid row fail the whole provider response with `MarketDataProviderError` instead of returning partial data.
- Include source, symbol, date range, row, column, invalid value, and reason in validation failure messages where applicable.
- Keep the public `MarketDataProvider` and `DailyPrice` contracts unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `market-data-provider`: AkShare normalization must reject invalid fetched行情 data with actionable provider-level errors.

## Impact

- Affected code: `packages/core/src/vela_core/akshare_market_data_provider.py`.
- Affected tests: AkShare provider normalization and error propagation tests.
- Public APIs: no signature or return type changes.
- Database/schema: no migration; invalid data is blocked before persistence.
