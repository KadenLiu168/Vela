## MODIFIED Requirements

### Requirement: API strategy signal latest endpoint
The API service SHALL expose `GET /api/strategy-signals/latest` returning the latest successful
strategy signal summary, metadata, and target positions scoped to the exact, case-sensitive current
`strategy_id` and `config_version`.

#### Scenario: Endpoint returns latest signal with positions
- **WHEN** a client requests `GET /api/strategy-signals/latest` and a successful signal exists for the current strategy id and config version
- **THEN** the response status is 200
- **AND** the response body includes `has_signal: true`, a `signal` object, and a `positions` array
- **AND** signals belonging to other strategies or config versions are ignored
- **AND** each position in the `positions` array includes the ETF's human-readable `name` (joined from `etf_info.name`), in addition to `exchange`, `symbol`, `target_weight`, `rank`, `score`, and `is_fallback`

#### Scenario: No successful signal returns empty state
- **WHEN** a client requests `GET /api/strategy-signals/latest` and no successful signal exists for the current strategy id and config version
- **THEN** the response status is 200
- **AND** the response body includes `has_signal: false`, a null `signal`, and an empty `positions` array
