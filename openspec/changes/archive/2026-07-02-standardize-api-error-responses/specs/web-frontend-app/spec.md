## ADDED Requirements

### Requirement: Frontend API error category mapping
The shared frontend API client SHALL parse stable API error envelopes and expose a readable error category for frontend code.

#### Scenario: Validation error is categorized
- **WHEN** the API returns a stable error envelope with `error.category` equal to `validation`
- **THEN** the shared API client rejects with an `ApiClientError` whose category is `validation`
- **AND** the error message is the readable API error message

#### Scenario: Not found error is categorized
- **WHEN** the API returns a stable error envelope with `error.category` equal to `not_found`
- **THEN** the shared API client rejects with an `ApiClientError` whose category is `not_found`
- **AND** the HTTP status remains available to page code

#### Scenario: Operation failed error is categorized
- **WHEN** the API returns a stable error envelope with `error.category` equal to `operation_failed`
- **THEN** the shared API client rejects with an `ApiClientError` whose category is `operation_failed`
- **AND** Dashboard operation feedback can render the readable reason

#### Scenario: Unexpected error is categorized
- **WHEN** the API returns a stable error envelope with `error.category` equal to `unexpected`
- **THEN** the shared API client rejects with an `ApiClientError` whose category is `unexpected`
- **AND** the frontend can show a generic readable failure state

### Requirement: Frontend real API error validation
The web frontend SHALL include validation for stable API error mapping that can run against real backend error responses.

#### Scenario: Local API error validation uses backend response shape
- **WHEN** frontend validation receives a stable error response produced by the local API error contract
- **THEN** the shared API client maps the response category and message without depending only on legacy `detail` strings
