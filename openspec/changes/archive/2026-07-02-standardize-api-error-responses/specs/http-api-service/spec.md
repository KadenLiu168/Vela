## ADDED Requirements

### Requirement: API stable error response envelope
The API service SHALL return non-2xx failures as a stable JSON object containing `error.code`, `error.category`, and `error.message`.

#### Scenario: Validation failure uses stable envelope
- **WHEN** a client sends an invalid request that fails FastAPI request validation
- **THEN** the response status is 422
- **AND** the response body contains `error.category` equal to `validation`
- **AND** the response body contains stable `error.code` and readable `error.message` fields

#### Scenario: Not found failure uses stable envelope
- **WHEN** a client requests a missing persisted resource
- **THEN** the response status is 404
- **AND** the response body contains `error.category` equal to `not_found`
- **AND** the response body contains stable `error.code` and readable `error.message` fields

#### Scenario: Operation failure uses stable envelope
- **WHEN** an API route detects an expected operation failure such as missing local market prices, invalid backtest dates, configuration loading failure, or provider workflow failure
- **THEN** the response body contains `error.category` equal to `operation_failed`
- **AND** the response body contains stable `error.code` and readable `error.message` fields

#### Scenario: Unexpected failure uses stable envelope
- **WHEN** an API route raises an otherwise unhandled exception
- **THEN** the response status is 500
- **AND** the response body contains `error.category` equal to `unexpected`
- **AND** the response body contains stable `error.code` and readable `error.message` fields

### Requirement: API error path integration validation
The API service SHALL validate stable error responses through real FastAPI routes and backend exception paths.

#### Scenario: Real route validation covers API errors
- **WHEN** the API error response tests run
- **THEN** they exercise real API route calls with `TestClient`
- **AND** they cover validation, not-found, no-market-data, date-range, configuration, provider workflow, and unexpected error paths
- **AND** they do not rely only on frontend request mocks
