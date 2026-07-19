## ADDED Requirements

### Requirement: API strategy signal list endpoint exposes provenance

`GET /api/strategy-signals` SHALL include `source` and `backtest_run_id` on each summary, in addition to the existing fields.

#### Scenario: List item includes provenance
- **WHEN** a client requests `GET /api/strategy-signals`
- **THEN** each entry in the `signals` array includes `source` (`manual`, `scheduled`, `backtest`, or `legacy`)
- **AND** each entry includes `backtest_run_id` (null for non-backtest and legacy signals)

#### Scenario: Existing list contract preserved
- **WHEN** a client requests `GET /api/strategy-signals`
- **THEN** the existing fields (`signal_id`, `signal_date`, `config_version`, `result`, `generated_at`, `is_fallback`, `position_count`) remain present
- **AND** ordering, scoping, limit, and offset behavior are unchanged

### Requirement: API strategy signal detail endpoint exposes provenance

`GET /api/strategy-signals/{signal_id}` SHALL include `source` and `backtest_run_id` in the signal metadata.

#### Scenario: Detail includes provenance
- **WHEN** a client requests an existing signal detail
- **THEN** the `signal` object includes `source` and `backtest_run_id`

### Requirement: API generate endpoint accepts caller source

`POST /api/strategy-signals/generate` SHALL accept an optional `source` query parameter (allowed `manual`, `scheduled`; default `manual`) and SHALL return the recorded `source` in the response. It SHALL reject `source="backtest"` or any other value with HTTP 400.

#### Scenario: Default generate source is manual
- **WHEN** a client posts without `source`
- **THEN** the response `source` is `manual`
- **AND** the existing response fields are unchanged

#### Scenario: Scheduled generate source is recorded
- **WHEN** a client posts with `source=scheduled`
- **THEN** the response `source` is `scheduled`
- **AND** the persisted signal row's `source` is `scheduled`

#### Scenario: Unsupported source rejected on generate
- **WHEN** a client posts with `source=backtest`, `source=legacy`, or another unsupported value
- **THEN** the endpoint returns HTTP 400 with the stable API error shape
- **AND** no signal row is persisted

### Requirement: API backtest detail endpoint lists its signals

`GET /api/backtests/{run_id}` SHALL include the ids of the strategy signals produced by that run.

#### Scenario: Backtest detail includes signal ids
- **WHEN** a client requests an existing backtest run detail
- **THEN** the top-level response includes `signal_ids`, an array of `strategy_signal.id` values ordered by `signal_date` then `id`
- **AND** the response includes `signal_count` equal to the length of `signal_ids`
- **AND** existing run/metrics/equity-curve fields are unchanged

#### Scenario: Backtest with no linked signals has an explicit empty collection
- **WHEN** a client requests an existing legacy or manually created backtest run with no linked signals
- **THEN** top-level `signal_ids` is an empty array
- **AND** top-level `signal_count` is `0`
