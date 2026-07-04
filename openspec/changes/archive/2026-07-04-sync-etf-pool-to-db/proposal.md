## Why

`fetch-market-data` reads active ETF metadata from the local `etf_info` table, but a freshly initialized database has no rows and there is no command that syncs the configured ETF universe from `config/etf_pool.yaml`. This makes the documented first-run workflow fail with `No active ETFs found`.

## What Changes

- Add an explicit CLI workflow, `uv run vela sync-etf-pool`, that loads the configured ETF pool and persists it into `etf_info`.
- Add a core synchronization service that upserts ETF metadata by `(exchange, symbol)`.
- Keep market data fetching explicit: `fetch-market-data` continues to read persisted active ETF rows and does not automatically sync configuration.
- Do not add a migration; the existing `ETFInfo` model already stores the configured fields needed for Phase 1.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `application-configuration`: ETF pool configuration can be used as the source for ETF metadata synchronization.
- `cli-database-initialization`: The project CLI exposes `sync-etf-pool` as a local setup command.
- `etf-info-model`: Persisted ETF metadata can be synchronized from the configured ETF pool.

## Impact

- Core package: add a small ETF pool to `ETFInfo` sync service and result type.
- CLI app: add `sync-etf-pool` command, arguments, output, and failure handling.
- Tests: add focused core and CLI coverage for insertion, update, idempotency, untouched out-of-pool rows, defaults, and failures.
