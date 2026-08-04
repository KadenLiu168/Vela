## ADDED Requirements

### Requirement: API lists current-strategy Walk-forward evaluations
The API SHALL expose `GET /api/walk-forwards` scoped to the configured `strategy_id`. It SHALL accept `limit` from 1 through 100 with default 10 and non-negative `offset` with default 0; it SHALL expose no `strategyId` filter. The response SHALL be `{ "runs": [...], "total": int, "limit": int, "offset": int }` with exact filtered total and summaries ordered by `finished_at` descending then `run_id` descending. Each summary SHALL contain `run_id`, `strategy_id`, `start_date`, `end_date`, `window_count`, `provenance_version`, `evidence_version`, `config_checksum`, `input_data_checksum`, `started_at` and `finished_at`. The endpoint MUST NOT start or mutate a Walk-forward execution.

#### Scenario: History returns a stable page and total
- **WHEN** a client requests `GET /api/walk-forwards?limit=10&offset=10`
- **THEN** the response contains at most ten current-strategy summaries from offset ten in stable order
- **AND** contains the exact current-strategy total, `limit=10` and `offset=10`

#### Scenario: Empty legacy history is explicit
- **WHEN** no persisted WF parent exists for the configured strategy
- **THEN** the endpoint returns `runs=[]`, `total=0` and the effective pagination values

#### Scenario: Invalid pagination is rejected
- **WHEN** limit is 0 or 101 or offset is negative
- **THEN** request validation returns status 422 through the standard validation error response

#### Scenario: Strategy filtering is not caller-selectable
- **WHEN** a client inspects the route signature and OpenAPI operation
- **THEN** no `strategyId` query parameter is present
- **AND** the configured strategy determines the complete list scope

### Requirement: API returns one typed Walk-forward evaluation detail
The API SHALL expose `GET /api/walk-forwards/{run_id}` scoped to the configured strategy. A successful response SHALL contain top-level `run`, `configuration`, `input_provenance`, `evidence_version`, `evidence` and `windows`. `run` SHALL contain `run_id`, `strategy_id`, `start_date`, `end_date`, `window_count`, `provenance_version`, `config_checksum`, `input_data_checksum`, `started_at`, `finished_at` and `created_at`. `configuration` SHALL be `{ "walk_forward": object, "base_strategy": object, "config_checksum": string }`. `input_provenance` SHALL be `{ "manifest": object, "input_data_checksum": string }`. `evidence` SHALL validate against `wf_evidence_v1`.

Windows SHALL be chronological and expose `ordinal`, `train_start`, `train_end`, `test_start`, `test_end`, `oos_version`, `selected_parameters`, `candidate_count`, `eligible_count`, `skipped_count`, `skip_reason_counts`, Decimal-string-or-null `train_sharpe` and `oos_backtest`. The OOS summary SHALL contain run id, strategy/config version, dates and status; Decimal-string-or-null total return, annualized return, Sharpe, maximum drawdown, volatility, Sortino and Calmar; integer-or-null longest-drawdown duration plus peak/trough/nullable-recovery dates; and exactly two benchmark groups containing the same persisted absolute encodings and duration dates plus Decimal-string-or-null strategy-relative return differences, Tracking Error and Information Ratio. The detail MUST NOT expose an OOS equity curve, concatenated series or cross-window path metric. Aggregate evidence values SHALL remain JSON numbers or null as defined by `wf_evidence_v1`.

#### Scenario: Detail exposes complete independent OOS evidence
- **WHEN** a client requests a persisted three-window evaluation
- **THEN** the response contains three ordered window records and their exact OOS backtest ids
- **AND** contains all strategy, dual-benchmark, active/downside risk, generalization and parameter-stability evidence
- **AND** contains no continuous OOS curve or cross-window path metric

#### Scenario: Decimal and aggregate number encodings are distinct
- **WHEN** detail contains persisted Backtest/window Decimal metrics and aggregate evidence statistics
- **THEN** persisted Decimal values serialize as strings or null
- **AND** aggregate summary/rate values serialize as JSON numbers or null

#### Scenario: Unknown or other-strategy run is not found
- **WHEN** a client requests a missing WF id or one owned by another strategy
- **THEN** the endpoint returns 404 through the standard API error envelope

#### Scenario: Corrupt evidence fails closed
- **WHEN** a current-strategy parent has an unsupported version or invalid persisted provenance/evidence document
- **THEN** the endpoint returns the standard unexpected-error response
- **AND** does not emit a partial detail

### Requirement: Walk-forward API is read-only
The HTTP service MUST NOT add an endpoint that starts, retries, edits or deletes a Walk-forward execution as part of this Change.

#### Scenario: OpenAPI exposes only history reads
- **WHEN** a client inspects Walk-forward paths in OpenAPI
- **THEN** only `GET /api/walk-forwards` and `GET /api/walk-forwards/{run_id}` are present

## MODIFIED Requirements

### Requirement: API strategy signal detail endpoint
The API service SHALL expose `GET /api/strategy-signals/{signal_id}` returning the metadata and target positions of one strategy signal by id, scoped to the current `strategy_id` regardless of `config_version`. Signal list/latest endpoints SHALL retain their current version-filtered behavior.

#### Scenario: Endpoint returns current-strategy signal detail across versions
- **WHEN** a client requests `GET /api/strategy-signals/{signal_id}` for an existing id that belongs to the current strategy, including a `wf-*` OOS signal
- **THEN** the response status is 200 regardless of that signal's config version
- **AND** the response body includes the signal metadata and a `positions` array
- **AND** each position in the `positions` array includes the ETF's human-readable `name` (joined from `etf_info.name`), in addition to `exchange`, `symbol`, `target_weight`, `rank`, `score`, and `is_fallback`

#### Scenario: Unknown signal id returns 404
- **WHEN** a client requests `GET /api/strategy-signals/{signal_id}` for an id that no row has
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

#### Scenario: Foreign-strategy signal id returns 404
- **WHEN** a client requests a signal id whose `strategy_id` differs from the current config
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

### Requirement: API backtest detail endpoint
The API service SHALL expose `GET /api/backtests/{run_id}` returning the detail of one backtest run by id, scoped to the current `strategy_id` regardless of `config_version`. Backtest list defaults and explicit version filters SHALL remain unchanged.

#### Scenario: Endpoint returns current-strategy run detail across versions
- **WHEN** a client requests `GET /api/backtests/{run_id}` for an existing id that belongs to the current strategy, including a `wf-*` OOS run
- **THEN** the response status is 200 regardless of that run's config version
- **AND** the response body includes run metadata (with `strategy_id` and `config_version`), metrics, and equity curve

#### Scenario: Unknown run id returns 404
- **WHEN** a client requests `GET /api/backtests/{run_id}` for an id that no row has
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

#### Scenario: Foreign-strategy run id returns 404
- **WHEN** a client requests a run id whose `strategy_id` differs from the current config
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

### Requirement: API backtest signals pagination endpoint
The API service SHALL expose `GET /api/backtests/{run_id}/signals` returning `{ "signals": [...] }` for signals linked to the given backtest run and scoped to the current `strategy_id` regardless of `config_version`. Each summary SHALL include `signal_id`, `signal_date`, `result`, and `backtest_run_id`. The endpoint SHALL return every signal linked to the run without a status filter, so for a stable run the collection across pages matches the `signal_count` returned by `GET /api/backtests/{run_id}`. Results SHALL be ordered by `signal_date` ascending then `id` ascending. The endpoint SHALL accept `limit` from 1 through 100 (default 20) and `offset >= 0`. Unknown runs and runs outside the current strategy SHALL return the same stable 404 shape.

#### Scenario: Endpoint returns paginated signal summaries across versions
- **WHEN** a client requests `GET /api/backtests/{run_id}/signals?limit=20&offset=0` for a current-strategy run, including a `wf-*` OOS run, with linked signals
- **THEN** the response status is 200 regardless of that run's config version
- **AND** the response body contains a `signals` array of at most 20 summaries
- **AND** each summary contains `signal_id`, `signal_date`, `result`, and `backtest_run_id`
- **AND** summaries are ordered by `signal_date` ascending then `signal_id` ascending

#### Scenario: Endpoint honors offset
- **WHEN** a client requests `GET /api/backtests/{run_id}/signals?limit=20&offset=40`
- **THEN** the response contains summaries starting at offset 40 in the stable ordering

#### Scenario: Unknown run id returns 404
- **WHEN** a client requests the endpoint for an id that no backtest run has
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

#### Scenario: Foreign strategy run returns 404
- **WHEN** a client requests the endpoint for a run whose `strategy_id` differs from the current config
- **THEN** the response status is 404
- **AND** the response body is indistinguishable from the unknown-run 404 response

#### Scenario: Invalid pagination is rejected
- **WHEN** a client supplies `limit=0`, `limit=101`, or a negative `offset`
- **THEN** the response status is 422
- **AND** the response body uses the stable API error shape with category `validation`

#### Scenario: Run with no linked signals returns empty collection
- **WHEN** a client requests the endpoint for an existing current-strategy run with no linked signals
- **THEN** the response status is 200
- **AND** the response body equals `{ "signals": [] }`

#### Scenario: Signal collection matches signal_count
- **WHEN** a client requests successive pages for a stable current-strategy run until exhausted
- **THEN** the concatenated signal ids contain no omissions or duplicates
- **AND** their total count equals the `signal_count` field of `GET /api/backtests/{run_id}`
