## Why

The web frontend needs a backend command endpoint that can trigger existing market price fetch workflows without shelling out to the CLI. COP-93 requires that endpoint to support both incremental and full fetch modes while returning the workflow statistics the frontend needs for status display.

## What Changes

- Add a market data fetch HTTP endpoint that accepts `mode=incremental|full`.
- Route the endpoint to the existing `fetch_incremental_market_prices` and `fetch_full_market_prices` core workflows.
- Return fetch status, requested ETF count, fetched/inserted/updated row counts, failed symbols, and error message.
- Validate the endpoint with a real FastAPI request, temporary SQLite database, and controlled provider.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `http-api-service`: Add a frontend-callable market data fetch command endpoint backed by existing core market data fetch workflows.

## Impact

- `apps/api`: Adds the HTTP route, provider dependency, and response serialization.
- `apps/api/tests`: Adds integration coverage using temporary SQLite and a controlled provider.
- `openspec/specs/http-api-service`: Extends API service requirements for the market data fetch endpoint.
