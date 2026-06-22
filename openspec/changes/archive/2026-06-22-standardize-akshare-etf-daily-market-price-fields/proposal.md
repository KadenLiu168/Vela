## Why

AkShare ETF daily prices are already normalized into provider-level `DailyPrice` values, but there is no explicit, tested mapping from those values into the internal `MarketPrice` persistence fields. The market data ingestion path needs a stable boundary so dates, prices, and volume keep clear Python types before database persistence.

## What Changes

- Add a small core mapping capability that converts normalized provider daily prices into `MarketPrice` ORM rows.
- Require the mapping to preserve `trade_date`, OHLC prices, optional `adjusted_close`, and optional `volume` with explicit field types.
- Keep AkShare-specific pandas column handling inside the existing AkShare provider; do not make the provider return ORM objects or require database sessions.
- Add tests covering the field mapping and the AkShare-to-`MarketPrice` normalization path through `DailyPrice`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `market-data`: Add a tested mapping from provider daily price values into internal `MarketPrice` fields.

## Impact

- Affected code: `packages/core/src/vela_core` market data mapping code and exports.
- Affected tests: core market data and AkShare provider tests.
- No database schema, Alembic migration, dependency, or public provider interface changes.
