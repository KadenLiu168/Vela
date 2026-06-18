## Why

Market data ingestion needs a durable audit trail before full and incremental fetch jobs grow beyond local experiments. Without a fetch log, failed or partial runs are hard to diagnose and later price data cannot be traced back to the job scope that produced it.

## What Changes

- Add a SQLAlchemy `DataFetchLog` ORM model for market data fetch task logging.
- Record each fetch task's source, target type, fetch mode, date range, requested symbols, lifecycle timestamps, status, result counts, and error message.
- Add indexes that support inspection by source, status, target, fetch mode, and run time.
- Add an Alembic migration and focused schema/index tests.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `market-data`: Add market data fetch logging requirements for tracking full and incremental fetch task scope, status, counts, and errors.

## Impact

- Core models: adds `DataFetchLog` under `packages/core/src/vela_core/models`.
- Database: adds a new `data_fetch_log` table through Alembic.
- Tests: adds focused model and migration-adjacent schema coverage under `packages/core/tests`.
- No ingestion provider client, scheduler, repository API, or strategy behavior is implemented by this change.
