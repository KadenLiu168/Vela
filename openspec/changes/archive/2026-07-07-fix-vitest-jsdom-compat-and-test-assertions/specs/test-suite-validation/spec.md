## MODIFIED Requirements

### Requirement: Frontend key component test validation

The repository SHALL include key frontend component-region validation in the configured frontend test suite.

#### Scenario: Frontend test suite validates key component regions

- **WHEN** a developer runs `npm --prefix apps/web run test` from the repository root
- **THEN** Vitest MUST execute frontend tests covering Dashboard status blocks, target holdings tables, backtest metric cards, and error summaries with zero failures
- **AND** those tests MUST use controlled fixtures whose field names and nesting match the real API response structures consumed by the shared frontend API client

#### Scenario: Frontend test suite validates key component states

- **WHEN** a developer runs `npm --prefix apps/web run test` from the repository root
- **THEN** Vitest MUST execute frontend tests covering loading, empty, and error states for the key frontend component regions with zero failures

#### Scenario: jsdom environment initializes reliably

- **WHEN** a developer runs `npm --prefix apps/web run test` from the repository root
- **THEN** the vitest jsdom environment SHALL initialize consistently across repeated runs
- **AND** no test SHALL fail with `document is not defined`

#### Scenario: Coverage timeline test assertions match current DOM structure

- **WHEN** Dashboard mock data includes non-null `earliest_trade_date` and `latest_trade_date`
- **THEN** tests SHALL query the timeline labels as `"Earliest"` and `"Latest"` (not `"trade date"`)
- **AND** when dates are null, tests SHALL verify the timeline is not rendered
