## ADDED Requirements

### Requirement: Backend entrypoints initialize shared logging

Backend executable entrypoints SHALL initialize the core `setup_logging()`
configuration before serving API requests or executing CLI operations.
Importing backend modules SHALL NOT configure global logging as a side effect.

#### Scenario: API startup configures logging
- **WHEN** the API executable starts the application server
- **THEN** it initializes the shared logging configuration before serving requests

#### Scenario: CLI startup configures logging
- **WHEN** the CLI executable begins command dispatch
- **THEN** it initializes the same shared logging configuration before executing the selected operation

#### Scenario: Module import has no logging side effect
- **WHEN** application or core modules are imported without invoking an executable entrypoint
- **THEN** they do not add or replace root logging handlers

### Requirement: Critical workflows emit lifecycle logs

Market-data fetching, strategy signal generation, and backtest execution SHALL
emit stable start and completion log events. Completion events SHALL include a
monotonic duration and bounded operation-relevant identifiers or counts.
Logging MUST occur at operation boundaries rather than once per price row,
holding, or rebalance date.

#### Scenario: Market-data fetch lifecycle is logged
- **WHEN** a market-data fetch operation completes
- **THEN** start and completion events identify the operation and provider
- **AND** the completion event records bounded ETF/row outcome counts and duration

#### Scenario: Signal-generation lifecycle is logged
- **WHEN** current or historical signal generation completes
- **THEN** start and completion events identify the strategy and requested date range
- **AND** the completion event records bounded signal or rebalance counts and duration

#### Scenario: Backtest lifecycle is logged
- **WHEN** a backtest completes
- **THEN** start and completion events identify the strategy and backtest date range
- **AND** the completion event records the run identifier, bounded result counts, and duration

#### Scenario: Hot loops do not log per item
- **WHEN** a multi-ETF or long-history operation runs
- **THEN** it does not emit one lifecycle log for every price row, holding, ETF, or rebalance date

### Requirement: Unexpected API failures retain correlated diagnostics

The backend SHALL record unexpected API failures with the effective request ID,
exception type, and stack trace while returning a generic non-sensitive
response to the client. Logs MUST NOT contain request bodies, credentials, or
database connection secrets.

#### Scenario: Unexpected exception is diagnosable
- **WHEN** an API operation raises an unexpected exception
- **THEN** the backend emits one exception diagnostic containing the request ID, exception type, and stack trace
- **AND** the client response does not contain the exception message or stack trace

#### Scenario: Expected failure does not produce an unexpected stack trace
- **WHEN** a typed expected domain failure is mapped to its stable HTTP response
- **THEN** the backend does not log it as an unexpected exception
