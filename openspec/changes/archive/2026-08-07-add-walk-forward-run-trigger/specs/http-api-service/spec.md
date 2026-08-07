## MODIFIED Requirements

### Requirement: Walk-forward API is read-only
The HTTP service SHALL expose `GET /api/walk-forwards`, `GET /api/walk-forwards/{run_id}`, and `POST /api/walk-forwards/run` for this history. The `POST /api/walk-forwards/run` endpoint SHALL be the only mutation route and SHALL only start a new asynchronous Walk-forward execution; the service MUST NOT add any endpoint that retries, edits, or deletes a Walk-forward execution, and MUST NOT expose any endpoint that mutates an existing `WalkForwardRun` row other than the status transition performed by the runner itself (`running` → `success` | `failed`).

#### Scenario: OpenAPI exposes only history reads
- **WHEN** a client inspects the Walk-forward read surface in OpenAPI
- **THEN** exactly the two GET history/detail paths are present and remain read-only
- **AND** no retry, edit, or delete path is present

#### Scenario: OpenAPI exposes history reads plus run trigger
- **WHEN** a client inspects Walk-forward paths in OpenAPI
- **THEN** exactly three Walk-forward paths are present: the two GET history/detail paths and one POST run-trigger path
- **AND** no retry, edit, or delete path is present

## ADDED Requirements

### Requirement: API triggers Walk-forward run asynchronously
The API service SHALL expose `POST /api/walk-forwards/run` with no request body and no query parameters. The endpoint SHALL load the walk-forward configuration path from the lifespan application configuration (MVP fixed to `config/walk_forward_v1.yaml`), execute `WalkForwardRunner.run()` off the event loop via `asyncio.to_thread`, and return HTTP 202 with a JSON body containing the positive `walk_forward_run_id` of a `WalkForwardRun` row whose `status` is `running`. The endpoint SHALL NOT block on completion of the run, SHALL NOT accept a client-supplied configuration path or file content, and SHALL NOT start a second run when the configured strategy already has a `running` record that is not stale. Expected domain failures (missing configuration, empty trading calendar, insufficient prices, no scorable combinations) SHALL use the existing typed domain error mapping with `validation` or `operation_failed` category; unexpected exceptions SHALL use the standard unexpected-error contract.

#### Scenario: Accepted run returns running identity
- **WHEN** a client posts to `/api/walk-forwards/run` against a database with sufficient market data and a valid walk-forward configuration
- **THEN** the response status is 202
- **AND** the response body contains a positive `walk_forward_run_id`
- **AND** a `WalkForwardRun` row with that id exists with `status = "running"` and a non-null `started_at`

#### Scenario: Missing market data returns structured error
- **WHEN** a client posts to `/api/walk-forwards/run` and the configured range has no local market prices
- **THEN** the response status is 400
- **AND** the response body uses the stable API error shape with category `operation_failed`
- **AND** no `WalkForwardRun` row with `status = "running"` is left persisted

#### Scenario: Client-supplied config path is rejected
- **WHEN** a client posts to `/api/walk-forwards/run?configPath=/etc/passwd` or supplies a config path in the request body
- **THEN** the response status is 422 or 400
- **AND** the response body uses the stable API error shape with category `validation`
- **AND** no walk-forward execution is started

#### Scenario: Concurrent run against non-stale running record is rejected
- **WHEN** a client posts to `/api/walk-forwards/run` while a current-strategy `WalkForwardRun` with `status = "running"` and `started_at` less than one hour ago already exists
- **THEN** the response status is 409
- **AND** the response body uses the stable API error shape with category `operation_failed`
- **AND** no second walk-forward execution is started

### Requirement: Walk-forward list and detail responses expose run status
`GET /api/walk-forwards` summary items and `GET /api/walk-forwards/{run_id}` run metadata SHALL include `status` (`running`, `success`, or `failed`) and nullable `error_message`. The list endpoint SHALL continue to scope by current `strategy_id`, retain stable `finished_at DESC, run_id DESC` ordering, and `running` records (with null `finished_at`) SHALL sort before any completed record by `started_at DESC`. Detail of a `running` record SHALL return complete metadata with null `finished_at`, empty `windows`, and the placeholder `evidence_version`/`evidence_json` written at start; Detail of a `failed` record SHALL return `error_message` and null `finished_at` only when the runner could not set it, otherwise the runner-set `finished_at`. Unknown and other-strategy ids SHALL use the standard 404 contract.

#### Scenario: Running record appears in list with status
- **WHEN** a `WalkForwardRun` with `status = "running"` exists for the current strategy
- **THEN** the list response includes that run with `status = "running"` and null `finished_at`
- **AND** it sorts before any completed run

#### Scenario: Failed record detail exposes error message
- **WHEN** a client requests the detail of a `WalkForwardRun` with `status = "failed"`
- **THEN** the response status is 200
- **AND** the run metadata includes `status = "failed"` and the persisted `error_message`
- **AND** `windows` is empty and `evidence` reflects the placeholder written at start

#### Scenario: Legacy success record backfilled by migration
- **WHEN** a client requests a `WalkForwardRun` persisted before this Change
- **THEN** the response metadata includes `status = "success"` and null `error_message`
- **AND** existing detail fields, windows, and evidence remain unchanged
