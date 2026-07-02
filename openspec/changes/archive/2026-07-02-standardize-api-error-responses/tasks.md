## 1. Backend Error Contract

- [x] 1.1 Add API error response helpers and exception handlers for validation, HTTP, expected operation, and unexpected failures.
- [x] 1.2 Convert current route-raised `HTTPException` and expected backend exceptions into stable error codes and categories.
- [x] 1.3 Add API tests using real `TestClient` route calls for validation, not-found, no-market-data, invalid date range, configuration, provider workflow, and unexpected error paths.

## 2. Frontend Error Mapping

- [x] 2.1 Extend `ApiClientError` to expose frontend-readable categories while preserving HTTP status and network kind.
- [x] 2.2 Parse stable API error envelopes in the shared API client with a fallback for legacy or malformed error bodies.
- [x] 2.3 Update Dashboard operation feedback to use normalized categories without changing successful operation behavior.
- [x] 2.4 Add frontend client and page tests for validation, not-found, operation-failed, unexpected, and network error behavior.

## 3. Validation

- [x] 3.1 Run focused backend API tests and frontend API tests.
- [x] 3.2 Run available backend and frontend lint/typecheck/test/build validation commands.
- [x] 3.3 Run OpenSpec validation for the change and affected capabilities.
