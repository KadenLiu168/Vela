## 1. Shared Database Defaults

- [x] 1.1 Add failing tests for a shared default local SQLite database URL.
- [x] 1.2 Move the default database URL to `vela_core.database` and update CLI imports.

## 2. API Database Session Dependency

- [x] 2.1 Add failing API integration tests for request success commit, request failure rollback, and route boundary.
- [x] 2.2 Configure the API app with an engine and session factory based on the shared default URL.
- [x] 2.3 Add a FastAPI database session dependency that reuses `managed_session`.

## 3. Documentation and Validation

- [x] 3.1 Document API database/session behavior.
- [x] 3.2 Run API tests, full backend validation, and OpenSpec validation.
