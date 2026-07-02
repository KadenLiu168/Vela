## 1. Frontend Tests

- [x] 1.1 Add Dashboard test coverage for manual refresh reloading `GET /api/dashboard` and rendering updated status values.
- [x] 1.2 Add Dashboard test coverage that a successful operation summary remains visible when the follow-up Dashboard refresh fails.
- [x] 1.3 Add Dashboard test coverage for empty-state copy pointing to matching local Dashboard actions.

## 2. Dashboard Implementation

- [x] 2.1 Add a manual Dashboard refresh action using the existing shared Dashboard API helper.
- [x] 2.2 Separate post-operation refresh failures from operation request failures.
- [x] 2.3 Align Dashboard empty-state copy with existing operation controls.

## 3. Validation

- [x] 3.1 Run focused frontend tests for Dashboard behavior.
- [x] 3.2 Run frontend lint/typecheck where available.
- [x] 3.3 Run OpenSpec validation for `improve-dashboard-refresh-empty-states`.
