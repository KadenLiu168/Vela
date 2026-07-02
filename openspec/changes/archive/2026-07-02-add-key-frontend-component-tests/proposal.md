## Why

COP-123 requires stronger frontend confidence around the critical workflow UI areas that users rely on during Phase 1 validation. Existing tests cover broad page behavior, but the OpenSpec contract should explicitly require controlled fixture coverage for key frontend component regions and their loading, empty, and error states.

## What Changes

- Add frontend tests that verify Dashboard status blocks, the target holdings table, backtest metric cards, and operation/API error summaries using controlled fixtures that match real API response structures.
- Extend frontend validation expectations so the standard web test command covers those key component regions across rendered, loading, empty, and error states.
- Keep the change limited to test coverage and OpenSpec documentation; no production API, backend model, database migration, dependency, or UI behavior changes are intended.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-frontend-app`: Require key frontend component-region coverage for Dashboard status blocks, target holdings, backtest metrics, and error summaries.
- `test-suite-validation`: Require the frontend test suite to include controlled fixture validation for those key component regions.

## Impact

- Affected frontend tests: `apps/web/src/App.test.tsx`.
- Affected OpenSpec capabilities: `web-frontend-app`, `test-suite-validation`.
- No API contract changes.
- No new runtime or test dependencies.
