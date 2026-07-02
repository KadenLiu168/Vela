## Why

Dashboard operation failures currently show normalized failure kinds such as `http` without explaining the API error reason or the user's next step. COP-116 requires market data fetch, signal generation, and backtest run failures to present user-understandable operation-level summaries while avoiding raw stack traces or database exception text as the only guidance.

## What Changes

- Render operation-specific failure summaries for market data fetch, signal generation, and backtest run request failures.
- Include the API-provided error reason when available, but pair it with concise local guidance for the next step.
- Keep raw stack traces and database exception text from being the only visible failure hint.
- Validate the failure states with tests that exercise real API error response bodies through the shared frontend API client path.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Add Dashboard operation-level error summary requirements for failed market data fetch, signal generation, and backtest run actions.

## Impact

- `apps/web/src/pages/DashboardPage.tsx`: operation error rendering and summary formatting.
- `apps/web/src/App.test.tsx`: Dashboard tests for real API error responses and operation-specific guidance.
- `openspec/specs/web-frontend-app/spec.md`: new requirement after archive.
- No backend API, database schema, or dependency changes.
