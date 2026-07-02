## ADDED Requirements

### Requirement: SQLite integration database preparation
The test support layer SHALL provide a reusable way to initialize a temporary or local SQLite database with the current ORM schema for integration validation.

#### Scenario: Temporary SQLite database is initialized
- **WHEN** an integration test requests a prepared SQLite database URL
- **THEN** the database MUST contain the current ORM tables
- **AND** the caller MUST receive a SQLAlchemy session factory for inspecting persisted rows

#### Scenario: Local SQLite database can be prepared for API acceptance
- **WHEN** a developer prepares a local SQLite database for API or frontend acceptance validation
- **THEN** the preparation flow MUST create or replace the SQLite schema at the requested database URL
- **AND** the prepared database MUST be usable by the local API service through the shared database URL configuration path

### Requirement: Minimal workflow dataset
The integration data preparation flow SHALL provide a deterministic minimal dataset covering ETF metadata, market prices, latest strategy signal data, and recent backtest data.

#### Scenario: Workflow data is seeded
- **WHEN** the workflow dataset is prepared in SQLite
- **THEN** the database MUST contain active ETF metadata rows
- **AND** it MUST contain enough market price history for signal generation and backtest execution validation
- **AND** it MUST contain persisted strategy signal and position rows for latest signal validation
- **AND** it MUST contain persisted backtest run and equity curve rows for backtest list, detail, and dashboard validation

### Requirement: Provider and persistence boundary
The integration data preparation flow SHALL make clear which integration validations use a controlled provider and which validations must use persisted SQLite rows.

#### Scenario: Market data fetch uses controlled provider
- **WHEN** an integration test validates market data fetch behavior
- **THEN** it MAY use a controlled market data provider
- **AND** it MUST verify resulting `MarketPrice` and `DataFetchLog` rows persisted to SQLite

#### Scenario: Read and workflow validations use persistence
- **WHEN** integration validation covers dashboard, latest signal, backtest list, backtest detail, signal generation, or backtest execution
- **THEN** the validation MUST use real SQLite persistence paths
- **AND** it MUST NOT rely only on frontend request mocks or mocked workflow return values

### Requirement: Reusable API and frontend acceptance setup
The integration data preparation flow SHALL be reusable by API tests and by frontend API acceptance validation.

#### Scenario: API tests reuse shared setup
- **WHEN** API integration tests need local workflow data
- **THEN** they MUST be able to prepare that data through shared test-support helpers instead of duplicating endpoint-local schema and seed functions

#### Scenario: Frontend API validation uses prepared backend state
- **WHEN** frontend API integration validation runs against a local FastAPI service
- **THEN** the validation path MUST document how to prepare the SQLite database before starting the API
- **AND** it MUST exercise API client calls against backend state prepared by the shared integration data flow
