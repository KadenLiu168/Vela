## Why

Vela needs a durable ETF metadata model before market data storage, querying, and strategy workflows can reference ETF identities consistently. The model should support international markets from the start so ticker symbols are not treated as globally unique.

## What Changes

- Add a SQLAlchemy ORM foundation that exposes declarative metadata for model registration and migrations.
- Add an `ETFInfo` ORM model covering core ETF identity and descriptive fields.
- Enforce ETF identity uniqueness by `exchange` and `symbol` rather than by symbol alone.
- Add indexes needed for common ETF metadata lookup and active-universe filtering.
- Add Alembic migration configuration so the model metadata can be discovered by autogenerate.
- Add focused tests for model metadata, constraints, indexes, and Alembic metadata discovery.

## Capabilities

### New Capabilities

- `etf-info-model`: SQLAlchemy ORM model and migration discovery contract for ETF metadata.

### Modified Capabilities

- None.

## Impact

- Affected code: `packages/core/src/vela_core`, `packages/core/tests`, Alembic configuration files, and migration environment files.
- Dependencies: introduces Alembic as a development/runtime migration tool if not already present.
- Systems: establishes the persistent ETF metadata table used by later market data, provider, strategy, and backtesting work.
- Non-goals: no repository API, no ETF import pipeline, no provider symbol mapping table, and no market price storage.
