## ADDED Requirements

### Requirement: API strategy signal list endpoint
The API service SHALL expose `GET /api/strategy-signals` returning a paginated list of successful strategy signal summaries scoped to the current `strategy_id` and `config_version`.

#### Scenario: Endpoint returns filtered summaries
- **WHEN** a client requests `GET /api/strategy-signals`
- **THEN** the response status is 200
- **AND** the response body includes a `signals` array of summaries whose `strategy_id` and `config_version` match the current strategy config
- **AND** only `success`-status signals are included
- **AND** summaries are ordered by `generated_at` descending then `id` descending

#### Scenario: Endpoint honors limit and offset
- **WHEN** a client requests `GET /api/strategy-signals?limit=20&offset=40`
- **THEN** the response contains at most 20 summaries starting at offset 40

#### Scenario: Empty history returns empty array
- **WHEN** a client requests `GET /api/strategy-signals` and no successful signal exists for the current strategy and version
- **THEN** the response body's `signals` array is empty

### Requirement: API strategy signal detail endpoint
The API service SHALL expose `GET /api/strategy-signals/{signal_id}` returning the metadata and target positions of one strategy signal by id, scoped to the current `strategy_id` and `config_version`.

#### Scenario: Endpoint returns signal detail
- **WHEN** a client requests `GET /api/strategy-signals/{signal_id}` for an existing id that belongs to the current strategy and version
- **THEN** the response status is 200
- **AND** the response body includes the signal metadata and a `positions` array

#### Scenario: Unknown signal id returns 404
- **WHEN** a client requests `GET /api/strategy-signals/{signal_id}` for an id that no row has
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

#### Scenario: Foreign-strategy signal id returns 404
- **WHEN** a client requests a signal id whose `strategy_id` or `config_version` differs from the current config
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

### Requirement: API backtest list endpoint
The API service SHALL expose `GET /api/backtests` returning a paginated list of backtest run summaries, filtered by `strategy_id` and `config_version` (defaulting to the current strategy config), ordered newest-started first.

#### Scenario: Endpoint returns summaries
- **WHEN** a client requests `GET /api/backtests`
- **THEN** the response status is 200
- **AND** the response body includes a `runs` array ordered by `started_at` descending then `id` descending
- **AND** each run summary includes `strategy_id` and `config_version`

#### Scenario: Endpoint defaults to current strategy filter
- **WHEN** a client requests `GET /api/backtests` without explicit filter params
- **THEN** only runs whose `strategy_id` and `config_version` match the current strategy config are included

#### Scenario: Endpoint honors limit and offset
- **WHEN** a client requests `GET /api/backtests?limit=10&offset=10`
- **THEN** the response contains at most 10 runs starting at offset 10

#### Scenario: Endpoint honors explicit strategy filter
- **WHEN** a client requests `GET /api/backtests?strategy_id=Dual_momentum&config_version=v1`
- **THEN** only runs matching both values are included

### Requirement: API backtest detail endpoint
The API service SHALL expose `GET /api/backtests/{run_id}` returning the detail of one backtest run by id, scoped to the current `strategy_id` and `config_version`.

#### Scenario: Endpoint returns run detail
- **WHEN** a client requests `GET /api/backtests/{run_id}` for an existing id that belongs to the current strategy and version
- **THEN** the response status is 200
- **AND** the response body includes run metadata (with `strategy_id`), metrics, and equity curve

#### Scenario: Unknown run id returns 404
- **WHEN** a client requests `GET /api/backtests/{run_id}` for an id that no row has
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

#### Scenario: Foreign-strategy run id returns 404
- **WHEN** a client requests a run id whose `strategy_id` or `config_version` differs from the current config
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`
