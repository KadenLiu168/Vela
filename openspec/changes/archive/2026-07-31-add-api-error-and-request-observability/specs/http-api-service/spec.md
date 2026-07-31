## ADDED Requirements

### Requirement: Expected API failures use typed domain mapping

The API service SHALL map expected domain failures by exception type through a
central transport-layer mapping. It MUST NOT choose an HTTP status, error code,
or error category by matching exception-message text, and it MUST NOT classify
an arbitrary `ValueError` as a client error. Existing specified failures MUST
retain their stable HTTP status and error-envelope semantics.

#### Scenario: Missing market data retains its contract
- **WHEN** strategy signal generation raises the typed missing-market-data error
- **THEN** the API returns status 400
- **AND** the response uses code `no_market_data` and category `operation_failed`
- **AND** the message states that no local market prices were found

#### Scenario: Invalid date range retains its contract
- **WHEN** an operation raises the typed invalid-date-range error
- **THEN** the API returns status 400
- **AND** the response uses code `invalid_date_range` and category `operation_failed`

#### Scenario: Error wording does not control classification
- **WHEN** an unclassified exception has the same message as a known domain error
- **THEN** the API does not map it as that known domain error
- **AND** the unexpected-error contract applies

#### Scenario: Arbitrary ValueError remains unexpected
- **WHEN** an endpoint or core operation raises a `ValueError` that is not a typed expected domain failure
- **THEN** the API returns status 500
- **AND** the response uses the generic unexpected-error envelope without exposing the exception detail

### Requirement: API requests are correlated by request ID

The API service SHALL assign one effective request ID to every request, expose
it in the `X-Request-ID` response header, and include it in the corresponding
request completion and unexpected-error logs. The service SHALL reuse a
caller-provided ID only when it satisfies the documented bounded safe-token
format; otherwise it SHALL generate a new UUID.

#### Scenario: Server generates a request ID
- **WHEN** a client sends a successful request without `X-Request-ID`
- **THEN** the response includes a non-empty `X-Request-ID` header
- **AND** the request completion log contains the same value

#### Scenario: Safe caller request ID is preserved
- **WHEN** a client supplies an allowed `X-Request-ID` value
- **THEN** the response header contains that same value
- **AND** request and exception logs for the request use that value

#### Scenario: Unsafe caller request ID is replaced
- **WHEN** a caller supplies an empty, over-length, or disallowed-character request ID
- **THEN** the service generates a different valid request ID
- **AND** the untrusted value is not emitted in logs

#### Scenario: Error responses remain correlated
- **WHEN** validation, typed-domain, explicit HTTP, or unexpected error handling produces a response
- **THEN** the response includes the effective `X-Request-ID`
- **AND** the existing JSON error-envelope fields and meanings remain unchanged

### Requirement: API request completion logs are bounded and safe

The API service SHALL emit one completion log per request containing the
effective request ID, HTTP method, normalized route template when available,
response status, and monotonic duration. Request completion logs MUST NOT
include request bodies, raw query strings, credentials, or exception details.

#### Scenario: Successful request emits completion context
- **WHEN** an API request completes successfully
- **THEN** exactly one request completion event records request ID, method, normalized route, status, and duration

#### Scenario: Failed request emits completion context
- **WHEN** an API request produces a handled or unexpected error response
- **THEN** exactly one request completion event records request ID, method, normalized route, status, and duration
- **AND** the event excludes the request body and raw query string
