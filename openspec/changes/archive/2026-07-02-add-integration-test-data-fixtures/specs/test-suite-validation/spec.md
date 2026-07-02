## ADDED Requirements

### Requirement: Shared integration data validation
The repository SHALL validate that shared integration test data setup can initialize SQLite and seed the minimal workflow dataset.

#### Scenario: Integration data setup is tested
- **WHEN** the Python test suite runs
- **THEN** it MUST validate that the shared integration data setup creates ORM tables and persists ETF, market price, strategy signal, and backtest rows in SQLite

### Requirement: Frontend API integration preparation path
The repository SHALL document a frontend API integration validation path that prepares SQLite backend state before frontend API client tests call the local FastAPI service.

#### Scenario: Frontend API integration path is documented
- **WHEN** a developer follows the frontend API integration validation documentation
- **THEN** they MUST be able to prepare deterministic local SQLite data before running `npm --prefix apps/web run test:integration:api`
- **AND** the documented flow MUST distinguish controlled provider validations from validations that require real persistence
