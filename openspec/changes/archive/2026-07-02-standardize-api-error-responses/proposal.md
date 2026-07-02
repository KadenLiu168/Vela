## Why

The API currently exposes multiple error shapes through FastAPI defaults or raw exception messages, which makes frontend operation feedback brittle. COP-117 requires stable backend JSON errors and frontend-readable categories for validation, not-found, operation-failed, and unexpected failures.

## What Changes

- Standardize API error responses into a JSON object with stable `error.code`, `error.category`, and `error.message` fields.
- Map backend validation, not-found, configuration, no-market-data, date-range, provider/workflow, and unexpected failures into predictable HTTP statuses and categories.
- Extend the frontend API client to parse the stable error shape and expose a readable `category` on `ApiClientError`.
- Update Dashboard operation feedback to use the normalized frontend error category while preserving existing scoped operation summaries.
- Add backend tests that exercise real FastAPI routes and exception paths instead of only mocking frontend fetch responses.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `http-api-service`: Add a stable API error response contract and integration validation for real backend exception paths.
- `web-frontend-app`: Extend shared API client HTTP error handling and Dashboard operation feedback to distinguish frontend-readable error categories.

## Impact

- Affected backend code: `apps/api/src/vela_api/main.py` and API tests.
- Affected frontend code: `apps/web/src/api/client.ts`, frontend API tests, and Dashboard operation feedback.
- Affected API contract: non-2xx responses return a stable `{"error": ...}` JSON object.
- Dependencies and database schema: no changes.
