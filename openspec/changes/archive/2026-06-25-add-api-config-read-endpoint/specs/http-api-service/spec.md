## ADDED Requirements

### Requirement: API config read endpoint
The API service SHALL expose `GET /api/config` as a read-only endpoint that returns the current strategy configuration summary and ETF pool summary.

#### Scenario: Config endpoint returns current strategy summary
- **WHEN** a client sends `GET /api/config`
- **THEN** the response status is 200 and the response includes the `strategy_id`, version, universe config path, momentum windows, score weights, trend filter, selection, defense asset, costs, and performance settings loaded from `config/strategy_v1.yaml`

#### Scenario: Config endpoint returns ETF pool summary
- **WHEN** a client sends `GET /api/config`
- **THEN** the response includes the ETF pool id, version, description, provider, currency, total ETF count, active ETF count, and ETF identity rows loaded from the configured ETF pool file

### Requirement: API config endpoint uses real config loading
The API config endpoint SHALL use the existing application configuration loader and checked-in configuration files instead of mock data.

#### Scenario: Config endpoint validates real checked-in configuration
- **WHEN** the config endpoint builds its response
- **THEN** it loads the current strategy config and referenced ETF pool through the existing `vela_core` configuration loading capability

### Requirement: API read-only config boundary
The API config endpoint SHALL NOT edit configuration files, calculate strategy outputs, or access the database.

#### Scenario: Config endpoint is read-only
- **WHEN** a client sends `GET /api/config`
- **THEN** the endpoint returns configuration summary data without mutating config files or requiring a database session
