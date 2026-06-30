## Why

Dashboard first-use states currently show that market data, signals, or backtests are missing, but they do not consistently explain what is missing and what local action should happen next. COP-92 requires those empty states to be clear for local first-time use and verified through real empty API data.

## What Changes

- Expand Dashboard empty states for missing market data, latest signal, and recent backtest data so each state describes the missing local data and the next local operation.
- Keep the empty states local-tool focused, with no login, multi-user, or deployment assumptions.
- Add API integration coverage for a real `GET /api/dashboard` response containing empty workflow data from an empty local SQLite database.

## Capabilities

### New Capabilities

### Modified Capabilities
- `web-frontend-app`: Clarify Dashboard empty-state requirements and validation for empty API data.
- `http-api-service`: Validate that the dashboard endpoint returns empty workflow values from a real empty local SQLite database.

## Impact

- Affected frontend files: `apps/web/src/pages/DashboardPage.tsx`, `apps/web/src/styles.css`, and frontend tests.
- Affected API tests: `apps/api/tests/test_dashboard.py`.
- Affected specs: `openspec/specs/web-frontend-app/spec.md` and `openspec/specs/http-api-service/spec.md` through delta specs.
- No backend API contract, database schema, or dependency changes are expected.
