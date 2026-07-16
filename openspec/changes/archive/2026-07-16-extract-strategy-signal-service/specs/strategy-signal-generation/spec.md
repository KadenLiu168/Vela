## ADDED Requirements

### Requirement: Generate and persist single-date strategy signal in core

The system SHALL provide a core service that generates and persists a single-date strategy signal from a SQLAlchemy session, a loaded strategy configuration, and an optional signal date. The service SHALL own the shared workflow for resolving the signal date, loading active ETFs, loading the price panel, building the defensive ETF lookup, invoking pure strategy signal generation, converting generated positions into persistence inputs, and persisting the signal result.

#### Scenario: Generate and persist using latest local market date
- **WHEN** backend code calls the core service without an explicit signal date and local market prices exist
- **THEN** the service uses the latest local `MarketPrice.trade_date` as the signal date
- **AND** the service persists one strategy signal row for the loaded strategy id and config version
- **AND** the service persists the generated signal positions
- **AND** the service returns a `GenerateStrategySignalResult` containing the persisted signal id

#### Scenario: Generate and persist using explicit signal date
- **WHEN** backend code calls the core service with an explicit signal date
- **THEN** the service generates and persists the strategy signal for that exact date
- **AND** the service does not replace the explicit date with the latest local market date

#### Scenario: Missing local market prices
- **WHEN** backend code calls the core service without an explicit signal date and no local market prices exist
- **THEN** the service raises a clear error indicating that no local market prices were found
- **AND** no strategy signal row is persisted

#### Scenario: Core service shares API and CLI persistence behavior
- **WHEN** the HTTP API endpoint and CLI command generate a strategy signal
- **THEN** both paths delegate signal workflow orchestration to the same core service
- **AND** both paths use the same active ETF loading, price panel loading, defensive lookup construction, persistence input conversion, and persistence behavior

### Requirement: Preserve pure strategy signal generation boundary

The system SHALL keep the pure strategy signal generation function separate from session-based persistence orchestration.

#### Scenario: Pure generation remains injected-input only
- **WHEN** backend code calls the pure strategy signal generation function
- **THEN** the function accepts injected active ETFs, price panel, defensive lookup, and strategy configuration
- **AND** the function does not require a database session
- **AND** the function does not issue `MarketPrice` queries during generation
