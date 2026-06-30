## Why

The Phase 1 frontend needs a local API action that can generate the latest strategy signal without shelling out to the CLI. Existing core signal generation already persists `StrategySignal` and positions, so the API should expose that capability through the FastAPI service.

## What Changes

- Add `POST /api/strategy-signals/generate` for generating and persisting a strategy signal.
- Accept optional query parameter `signalDate` in `YYYY-MM-DD` format.
- When `signalDate` is omitted, infer the signal date from the latest local `MarketPrice.trade_date`.
- Load the current strategy config through the existing checked-in config path and call the existing `generate_strategy_signal` core function.
- Return signal id, signal date, config version, status, result, error message, and generated positions.
- Validate the endpoint through local FastAPI + SQLite integration tests that use the real core generation workflow instead of only mocked results.
- Do not use a JSON request body schema for this endpoint.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `http-api-service`: Add a local strategy signal generation command endpoint backed by existing core signal generation and SQLite persistence.

## Impact

- Affected API: new `POST /api/strategy-signals/generate?signalDate=YYYY-MM-DD`.
- Affected code: FastAPI route wiring in `apps/api`, using existing `vela_core.generate_strategy_signal`.
- Affected tests: API integration tests with temporary SQLite databases and persisted ORM rows.
- No database migration or new dependency is expected.
