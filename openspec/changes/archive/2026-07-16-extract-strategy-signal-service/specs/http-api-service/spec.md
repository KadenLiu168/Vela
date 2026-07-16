## ADDED Requirements

### Requirement: API delegates strategy signal generation orchestration to core

The API service SHALL expose the strategy signal generation endpoint while delegating business workflow orchestration to the core strategy signal service. The endpoint SHALL remain responsible for HTTP query parameter handling, HTTP error mapping, and response formatting.

#### Scenario: Generate endpoint preserves successful response contract
- **WHEN** a client posts to `/api/strategy-signals/generate` and local market data is available
- **THEN** the endpoint returns status 200
- **AND** the response body includes the existing strategy signal response fields: `signal_id`, `signal_date`, `config_version`, `status`, `result`, `error_message`, and `positions`
- **AND** the signal generation and persistence workflow is performed by the core service

#### Scenario: Generate endpoint preserves explicit signal date behavior
- **WHEN** a client posts to `/api/strategy-signals/generate?signalDate=<date>`
- **THEN** the endpoint passes the parsed signal date to the core service
- **AND** the response reports that same signal date when generation succeeds

#### Scenario: Generate endpoint preserves missing market data error
- **WHEN** a client posts to `/api/strategy-signals/generate` and no local market prices exist
- **THEN** the endpoint returns status 400
- **AND** the response uses the stable API error shape with category `operation_failed`
- **AND** the error message states that no local market prices were found

#### Scenario: Transport layer does not duplicate core signal workflow
- **WHEN** maintainers inspect the API strategy signal generation endpoint
- **THEN** the endpoint does not directly load active ETFs, load price panels, build defensive ETF lookup maps, construct signal persistence callbacks, or convert generated positions into persistence inputs
