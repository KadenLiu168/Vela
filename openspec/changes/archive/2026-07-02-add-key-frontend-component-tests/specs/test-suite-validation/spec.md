## ADDED Requirements

### Requirement: Frontend key component test validation
The repository SHALL include key frontend component-region validation in the configured frontend test suite.

#### Scenario: Frontend test suite validates key component regions
- **WHEN** a developer runs `npm --prefix apps/web run test` from the repository root
- **THEN** Vitest MUST execute frontend tests covering Dashboard status blocks, target holdings tables, backtest metric cards, and error summaries
- **AND** those tests MUST use controlled fixtures whose field names and nesting match the real API response structures consumed by the shared frontend API client

#### Scenario: Frontend test suite validates key component states
- **WHEN** a developer runs `npm --prefix apps/web run test` from the repository root
- **THEN** Vitest MUST execute frontend tests covering loading, empty, and error states for the key frontend component regions
