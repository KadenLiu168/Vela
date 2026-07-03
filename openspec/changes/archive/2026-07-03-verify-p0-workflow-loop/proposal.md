## Why

COP-127 is the P0 acceptance gate for the first-version local research workflow. The individual market data, signal generation, and backtest loops are now validated separately, but the project still needs one full workflow validation that proves the same persisted backend state supports the Dashboard and detail reads after refresh.

## What Changes

- Add an API integration test that performs the P0 workflow through real API endpoints: read Dashboard, fetch market data, generate a signal, run a backtest, and read the generated backtest detail.
- Verify each operation uses existing backend workflows and persists state that can be read again through follow-up API requests.
- Add persisted Dashboard summary detail links so users can open Signal Detail and Backtest Detail after a Dashboard refresh, not only immediately after an operation result.
- Record that no blocking backend gaps or API field mismatches were found for the tested P0 workflow.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `http-api-service`: Require a full P0 workflow validation across Dashboard, market data fetch, signal generation, backtest run, and backtest detail reads.
- `web-frontend-app`: Require Dashboard persisted summaries to expose detail entry points for the latest signal and recent backtest.
- `test-suite-validation`: Require pytest coverage for the COP-127 full P0 workflow loop.

## Impact

- Affected frontend: `apps/web/src/pages/DashboardPage.tsx`
- Affected tests: new API workflow test under `apps/api/tests`, frontend Dashboard tests
- Affected OpenSpec files: `http-api-service`, `test-suite-validation`
- No API contract changes.
- No new dependencies.
