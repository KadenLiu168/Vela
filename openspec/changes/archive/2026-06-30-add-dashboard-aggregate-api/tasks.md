## 1. Tests

- [x] 1.1 Add focused core dashboard aggregation tests for empty data and populated SQLite ORM rows.
- [x] 1.2 Add API integration tests that configure a temporary SQLite database and call `GET /api/dashboard` through `TestClient`.

## 2. Core Implementation

- [x] 2.1 Implement `vela_core` dashboard aggregation dataclasses and query service.
- [x] 2.2 Ensure dates, datetimes, and decimals are converted to JSON-compatible values in the aggregate response.

## 3. API Implementation

- [x] 3.1 Add `GET /api/dashboard` using the existing database session dependency.
- [x] 3.2 Keep existing health and config endpoints behavior unchanged.

## 4. Validation

- [x] 4.1 Run focused dashboard API/core tests.
- [x] 4.2 Run applicable full test, lint, format/type-check, and OpenSpec validation commands.
