## Why

COP-124 requires validation that the frontend market data fetch path is backed by the real API workflow, persisted SQLite rows, and refreshed Dashboard state. The implementation already has the pieces, but the backend validation currently tests fetch persistence and Dashboard reads separately rather than proving the closed loop in one flow.

## What Changes

- Add an API integration test that posts to the market data fetch endpoint and then reads the Dashboard endpoint from the same temporary SQLite database.
- Verify the fetch endpoint uses the existing market data workflow to insert or update `MarketPrice` rows and record a `DataFetchLog`.
- Verify the follow-up Dashboard response reflects the newly persisted market data status and operation summary.
- Keep frontend behavior unchanged because the Dashboard already calls the shared fetch client and reloads `GET /api/dashboard` after success.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `http-api-service`: Require a closed-loop validation that market data fetch persistence is visible through the Dashboard API refresh source.
- `test-suite-validation`: Require the pytest suite to include the COP-124 market data fetch to Dashboard closed-loop validation.

## Impact

- Affected tests: `apps/api/tests/test_market_data_fetch.py`
- Affected OpenSpec files: `http-api-service`, `test-suite-validation`
- No API contract changes.
- No new dependencies.
