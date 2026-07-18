## MODIFIED Requirements

### Requirement: API strategy signal detail endpoint
The API service SHALL expose `GET /api/strategy-signals/{signal_id}` returning the metadata and target positions of one strategy signal by id, scoped to the current `strategy_id` and `config_version`.

#### Scenario: Endpoint returns signal detail
- **WHEN** a client requests `GET /api/strategy-signals/{signal_id}` for an existing id that belongs to the current strategy and version
- **THEN** the response status is 200
- **AND** the response body includes the signal metadata and a `positions` array
- **AND** each position in the `positions` array includes the ETF's human-readable `name` (joined from `etf_info.name`), in addition to `exchange`, `symbol`, `target_weight`, `rank`, `score`, and `is_fallback`

#### Scenario: Unknown signal id returns 404
- **WHEN** a client requests `GET /api/strategy-signals/{signal_id}` for an id that no row has
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

#### Scenario: Foreign-strategy signal id returns 404
- **WHEN** a client requests a signal id whose `strategy_id` or `config_version` differs from the current config
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

## ADDED Requirements

### Requirement: API strategy signal latest endpoint
The API service SHALL expose `GET /api/strategy-signals/latest` returning the latest successful strategy signal summary, metadata, and target positions scoped to the current `config_version`.

#### Scenario: Endpoint returns latest signal with positions
- **WHEN** a client requests `GET /api/strategy-signals/latest` and a successful signal exists for the current config version
- **THEN** the response status is 200
- **AND** the response body includes `has_signal: true`, a `signal` object, and a `positions` array
- **AND** each position in the `positions` array includes the ETF's human-readable `name` (joined from `etf_info.name`), in addition to `exchange`, `symbol`, `target_weight`, `rank`, `score`, and `is_fallback`

#### Scenario: No successful signal returns empty state
- **WHEN** a client requests `GET /api/strategy-signals/latest` and no successful signal exists for the current config version
- **THEN** the response status is 200
- **AND** the response body includes `has_signal: false`, a null `signal`, and an empty `positions` array
