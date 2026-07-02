## Why

COP-121 requires first-version API interface tests that validate response structures and important error paths through the real FastAPI app. Existing endpoint tests cover many behaviors, but the API test contract should be explicit and complete across health, config, dashboard, fetch, signal, and backtest endpoints.

## What Changes

- Add focused API contract tests for the first-version endpoint surface, covering success responses, empty-data responses, not-found responses, request validation failures, configuration failures, date-range failures, and controlled provider failures.
- Reuse temporary SQLite databases and the shared integration data helpers so tests exercise real API routes and backend persistence paths instead of only mocking `vela_core` workflows.
- Document the API contract validation requirement in the HTTP API service spec and include it in the repository test-suite validation contract.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `http-api-service`: Add explicit API contract validation requirements for endpoint response shapes and key error paths.
- `test-suite-validation`: Require the Python test suite to include the API contract validation coverage.

## Impact

- Affected tests: `apps/api/tests/`
- Affected OpenSpec specs: `openspec/specs/http-api-service/spec.md`, `openspec/specs/test-suite-validation/spec.md`
- No production API routes, ORM models, migrations, or new runtime dependencies are expected.
