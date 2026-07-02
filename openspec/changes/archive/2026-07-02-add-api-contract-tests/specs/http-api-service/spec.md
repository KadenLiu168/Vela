## ADDED Requirements

### Requirement: API first-version interface contract validation
The API service SHALL validate the first-version API interface surface through real FastAPI route calls.

#### Scenario: Interface tests cover first-version endpoint success responses
- **WHEN** the API interface contract tests run
- **THEN** they MUST call `GET /api/health`, `GET /api/config`, `GET /api/dashboard`, `POST /api/market-data/fetch`, `POST /api/strategy-signals/generate`, `GET /api/strategy-signals/latest`, `GET /api/backtests`, `POST /api/backtests/run`, and `GET /api/backtests/{run_id}` through `TestClient`
- **AND** they MUST assert stable top-level response structures for each successful endpoint family

#### Scenario: Interface tests cover empty persistence states
- **WHEN** the API interface contract tests run against an empty temporary SQLite database
- **THEN** they MUST validate stable empty response structures for dashboard, latest signal, and backtest list endpoints
- **AND** they MUST not rely only on mocked backend return values

#### Scenario: Interface tests cover key API error paths
- **WHEN** the API interface contract tests run
- **THEN** they MUST validate request validation, missing resource, missing market data, invalid date range, configuration failure, and provider workflow failure paths
- **AND** non-2xx failures MUST use the stable `error.code`, `error.category`, and `error.message` response envelope

#### Scenario: Interface tests exercise real backend paths
- **WHEN** API interface tests cover dashboard, latest signal, backtest list, backtest detail, signal generation, or backtest execution
- **THEN** they MUST use temporary SQLite data and existing backend workflows or persisted ORM rows
- **AND** market data fetch tests MAY use a controlled provider but MUST verify the resulting response and persistence behavior through the API route
