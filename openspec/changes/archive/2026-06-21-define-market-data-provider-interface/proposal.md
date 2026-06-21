## Why

Vela needs a small market data provider contract before adding concrete data sources such as AkShare. Defining the provider boundary now keeps ETF daily market data ingestion testable and prevents provider-specific return shapes from leaking into core workflows.

## What Changes

- Add a `MarketDataProvider` abstraction for fetching ETF daily OHLCV data.
- Add a normalized provider-level daily price value object that is independent of pandas, AkShare, and SQLAlchemy ORM models.
- Establish that provider implementations can be replaced with fake providers in tests.
- Keep AkShare implementation, persistence/upsert behavior, and provider symbol mapping out of this change.

## Capabilities

### New Capabilities
- `market-data-provider`: Defines the provider abstraction and normalized ETF daily price contract used by future market data ingestion.

### Modified Capabilities

## Impact

- Affected code: `packages/core/src/vela_core/` provider-facing modules and focused core tests.
- Public API: introduces a typed provider contract and daily price DTO for core backend code.
- Dependencies: no new runtime dependency is required.
- Systems: prepares future AkShare integration while keeping the core contract provider-agnostic.
