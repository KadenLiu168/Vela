## Why

COP-122 needs an explicit frontend build acceptance path so the first-version web frontend cannot regress into a state that only works under the development server or local mocks. The repository already has web `typecheck` and `build` commands, but the acceptance contract should name them directly and document that they do not require a local API or mock service.

## What Changes

- Make frontend TypeScript type checking an explicit repository validation expectation through `npm --prefix apps/web run typecheck`.
- Make frontend production build acceptance an explicit repository validation expectation through `npm --prefix apps/web run build`.
- Clarify that frontend build/typecheck validation must complete without a running local API service, local mock service, or API integration test setup.
- Document the frontend build acceptance command sequence alongside existing web validation guidance.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `test-suite-validation`: Add explicit frontend TypeScript and production build validation requirements.
- `web-frontend-app`: Clarify that web build validation commands complete without backend or mock services.

## Impact

- Affected documentation: `apps/web/README.md`.
- Affected OpenSpec specs: `test-suite-validation`, `web-frontend-app`.
- Affected validation commands: `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run build`.
- No backend API, database model, migration, runtime dependency, or production frontend behavior changes.
