## Why

API and frontend acceptance tests currently prepare local SQLite data through ad hoc helpers or require an already-running API with unspecified state. COP-120 needs a shared, repeatable data preparation flow so integration validation can exercise real persistence paths instead of stopping at frontend mocks.

## What Changes

- Add a reusable integration test data preparation capability for temporary or local SQLite databases.
- Provide a minimal deterministic ETF, market price, signal, and backtest dataset that API tests and frontend API acceptance tests can reuse.
- Document which validation paths may use controlled providers and which paths must read or write through SQLite persistence.
- Wire existing API tests and the frontend API integration validation path to the shared preparation flow without changing production API contracts.

## Capabilities

### New Capabilities
- `integration-test-data`: Shared preparation of deterministic SQLite integration data for API and frontend acceptance validation.

### Modified Capabilities
- `test-suite-validation`: Validation expectations now include the shared integration test data preparation flow and frontend API integration reuse.

## Impact

- Adds test support code for SQLite database initialization and seeded workflow data.
- Updates API integration tests to reuse shared setup helpers where they currently duplicate setup.
- Updates frontend API integration validation documentation and test setup to support a prepared local API database.
- No production endpoint, database schema, dependency, or runtime behavior change is intended.
