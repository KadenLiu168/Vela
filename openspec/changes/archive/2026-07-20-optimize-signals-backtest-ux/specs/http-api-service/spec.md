## MODIFIED Requirements

### Requirement: API strategy signal list endpoint
The API service SHALL expose `GET /api/strategy-signals` returning a paginated list of successful strategy signal summaries scoped to the current `strategy_id` and `config_version`. The endpoint SHALL accept an optional `source` query parameter filtering by `manual`, `scheduled`, `backtest`, or `legacy`. Omitting `source` SHALL return signals of all sources. Any supplied value outside the four-value enum, including an empty value or the string `null`, SHALL be rejected at the query-parameter layer with 422.

#### Scenario: Endpoint returns filtered summaries
- **WHEN** a client requests `GET /api/strategy-signals`
- **THEN** the response status is 200
- **AND** the response body includes a `signals` array of summaries whose `strategy_id` and `config_version` match the current strategy config
- **AND** only `success`-status signals are included
- **AND** summaries are ordered by `generated_at` descending then `id` descending

#### Scenario: Endpoint honors limit and offset
- **WHEN** a client requests `GET /api/strategy-signals?limit=20&offset=40`
- **THEN** the response contains at most 20 summaries starting at offset 40

#### Scenario: Source filter narrows results
- **WHEN** a client requests `GET /api/strategy-signals?source=backtest`
- **THEN** every entry in the `signals` array has `source` equal to `backtest`
- **AND** entries whose `source` is not `backtest` are excluded before limit and offset are applied

#### Scenario: Every declared source is accepted
- **WHEN** a client requests the endpoint once for each value in `StrategySignal.SOURCES`
- **THEN** each request passes query validation
- **AND** any returned entry has the requested source

#### Scenario: Invalid source is rejected
- **WHEN** a client supplies an unknown, empty, or literal `null` source value
- **THEN** the response status is 422
- **AND** the response body uses the stable API error shape with category `validation`

#### Scenario: Empty history returns empty array
- **WHEN** a client requests `GET /api/strategy-signals` and no successful signal exists for the current strategy and version
- **THEN** the response body's `signals` array is empty

## ADDED Requirements

### Requirement: API backtest signals pagination endpoint
The API service SHALL expose `GET /api/backtests/{run_id}/signals` returning `{ "signals": [...] }` for signals linked to the given backtest run and scoped to the current `strategy_id` and `config_version`. Each summary SHALL include `signal_id`, `signal_date`, `result`, and `backtest_run_id`. The endpoint SHALL return every signal linked to the run without a status filter, so for a stable run the collection across pages matches the `signal_count` returned by `GET /api/backtests/{run_id}`. Results SHALL be ordered by `signal_date` ascending then `id` ascending. The endpoint SHALL accept `limit` from 1 through 100 (default 20) and `offset >= 0`. Unknown runs and runs outside the current strategy or config version SHALL return the same stable 404 shape.

#### Scenario: Endpoint returns paginated signal summaries
- **WHEN** a client requests `GET /api/backtests/{run_id}/signals?limit=20&offset=0` for an in-scope run with linked signals
- **THEN** the response status is 200
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

#### Scenario: Foreign strategy or config run returns 404
- **WHEN** a client requests the endpoint for a run whose `strategy_id` or `config_version` differs from the current config
- **THEN** the response status is 404
- **AND** the response body is indistinguishable from the unknown-run 404 response

#### Scenario: Invalid pagination is rejected
- **WHEN** a client supplies `limit=0`, `limit=101`, or a negative `offset`
- **THEN** the response status is 422
- **AND** the response body uses the stable API error shape with category `validation`

#### Scenario: Run with no linked signals returns empty collection
- **WHEN** a client requests the endpoint for an existing in-scope run with no linked signals
- **THEN** the response status is 200
- **AND** the response body equals `{ "signals": [] }`

#### Scenario: Signal collection matches signal_count
- **WHEN** a client requests successive pages for a stable in-scope run until exhausted
- **THEN** the concatenated signal ids contain no omissions or duplicates
- **AND** their total count equals the `signal_count` field of `GET /api/backtests/{run_id}`
