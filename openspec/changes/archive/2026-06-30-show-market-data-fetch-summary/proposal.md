## Why

Dashboard can trigger the incremental market data fetch operation, but it currently only refreshes data or shows a generic request failure. COP-95 needs the frontend to show the real fetch result summary so users can see what changed and what to do when symbols fail.

## What Changes

- Show a Dashboard operation result summary after the market data fetch request completes.
- On successful responses, show fetched, inserted, and updated row counts from the API response.
- On `partial` or `failed` responses, show failed symbols and the API error summary.
- Use retry and local data/source guidance in failure copy.
- Validate success, partial, and failed response rendering through the existing real API response contract.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Extend Dashboard market data fetch behavior to render operation result summaries from the fetch API response.

## Impact

- Affected frontend code: `apps/web/src/pages/DashboardPage.tsx` and related frontend tests.
- Uses the existing shared client helper and COP-93 API response fields.
- No backend API contract changes, new dependencies, or COP-93/COP-94 reimplementation are expected.
