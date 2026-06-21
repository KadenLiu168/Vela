## Why

Vela already has a provider abstraction for normalized ETF daily prices, but no production data source implementation. Implementing an AkShare-backed provider lets market data ingestion fetch real ETF daily行情 while preserving the internal `DailyPrice` contract.

## What Changes

- Add an `AkShareMarketDataProvider` that fetches ETF daily prices through AkShare `fund_etf_hist_em`.
- Normalize AkShare's Chinese-column DataFrame output into internal `DailyPrice` values.
- Use unadjusted prices by default, leaving `adjusted_close` as `None`.
- Add stable provider-level errors that upper-layer fetch workflows can catch and record in `DataFetchLog`.
- Add `akshare` as a project dependency.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `market-data-provider`: Add a concrete AkShare ETF daily price provider requirement and provider error behavior.

## Impact

- Affected package: `packages/core`.
- Public API: exports a concrete AkShare market data provider and provider error type.
- Dependency changes: adds `akshare`.
- Systems: enables future ingestion code to fetch real ETF daily OHLCV rows while keeping database logging outside the provider layer.
