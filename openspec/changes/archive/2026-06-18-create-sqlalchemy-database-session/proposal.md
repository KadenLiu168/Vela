## Why

Vela needs a reliable database session foundation before market data storage, querying, and later backtesting workflows can safely use SQLAlchemy. Without a shared session boundary, persistence code will either duplicate setup logic or risk inconsistent transaction handling.

## What Changes

- Add a SQLAlchemy database session capability for the core backend package.
- Provide a single place to create the database engine and session factory from application configuration.
- Provide a context-managed session boundary that commits successful work, rolls back failed work, and closes sessions.
- Add tests covering session creation and transaction behavior.

## Capabilities

### New Capabilities

- `database-session`: SQLAlchemy engine, session factory, and context-managed session lifecycle for backend persistence code.

### Modified Capabilities

- None.

## Impact

- Affected code: `packages/core/src` and `packages/core/tests`.
- Dependencies: uses the existing `sqlalchemy` dependency from `pyproject.toml`.
- Systems: establishes the persistence foundation for later ETF metadata and market price storage work.
