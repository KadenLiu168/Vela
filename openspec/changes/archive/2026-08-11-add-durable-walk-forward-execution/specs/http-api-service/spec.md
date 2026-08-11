## MODIFIED Requirements

### Requirement: API lists current-strategy Walk-forward evaluations
The API SHALL expose `GET /api/walk-forwards` scoped to the configured `strategy_id`, with `limit` 1..100 (default 10), non-negative `offset` (default 0), and exact total. It SHALL return queued/running records before terminal records, ordered by `started_at DESC, run_id DESC`, followed by terminal records ordered by `finished_at DESC, run_id DESC`. Every item SHALL expose status (`queued`, `running`, `success`, or `failed`), attempt count, claimed timestamp, heartbeat timestamp, and lease expiry, and SHALL not expose a worker identity or claim token. It SHALL expose no `strategyId` filter and MUST NOT start or mutate a Walk-forward execution.

#### Scenario: History returns a stable page and total
- **WHEN** a client requests `GET /api/walk-forwards?limit=10&offset=10`
- **THEN** the response contains at most ten current-strategy summaries and the exact current-strategy total

#### Scenario: Active execution sorts before completed history
- **WHEN** queued, running, and completed records exist for the current strategy
- **THEN** queued/running records appear before completed records with their lifecycle fields
- **AND** no item includes a claim token or worker identity

### Requirement: API returns one typed Walk-forward evaluation detail
The API SHALL expose `GET /api/walk-forwards/{run_id}` with typed ISO dates/timestamps, lifecycle status/attempt/lease metadata, persisted decimal strings, provenance/evidence versions and checksums, manifest, aggregate evidence, ordered windows, OOS links, fixed benchmark data, and a non-null `stitched_oos` result derived from authoritative persisted evidence for successful records. `stitched_oos.status` SHALL be `available` when the windows are contiguous or `unavailable_non_contiguous_windows` when otherwise valid windows have a gap or overlap. An available result SHALL contain Decimal strings `initial_net_value`, `ending_net_value`, and `total_return`, plus chronological `points`; every point SHALL contain ISO `trade_date`, six-place Decimal-string `net_value`, integer `window_ordinal`, and boolean `is_window_start`. An unavailable result SHALL contain null cumulative values and an empty points list while the rest of the detail remains complete. Queued, running, and failed records SHALL return their captured configuration/provenance and lifecycle fields with `evidence = null`, `stitched_oos = null`, and empty windows; they SHALL not validate placeholder evidence or fabricate an OOS result. Unknown and other-strategy ids SHALL use the standard 404 contract. Unsupported or corrupt persisted documents, OOS ownership, eligible source curves, or official-session manifests on a successful record SHALL use the standard unexpected-error contract without partial detail data.

#### Scenario: Detail preserves ordered ownership
- **WHEN** a current-strategy persisted successful evaluation with valid adjacent OOS windows is requested
- **THEN** each window exposes its selected OOS run and both fixed benchmarks in chronological order
- **AND** `stitched_oos.status` is `available` and exposes the deterministic compounded points and cumulative result in the same window order

#### Scenario: Active detail does not fabricate execution evidence
- **WHEN** a client requests a queued or running current-strategy record
- **THEN** the response contains captured metadata and lifecycle fields with null evidence, null stitched OOS, and empty windows
- **AND** it does not validate placeholder evidence or return partial OOS artifacts

#### Scenario: Reset boundary is machine-readable
- **WHEN** a successful Walk-forward detail contains more than one stitched OOS segment
- **THEN** the first point for each segment identifies its owning `window_ordinal` and has `is_window_start = true`
- **AND** every later point in that segment has `is_window_start = false`

#### Scenario: Invalid stitched evidence returns no partial detail
- **WHEN** contiguous persisted successful windows are eligible for stitching but their OOS curves or official-session manifest is corrupt
- **THEN** the API returns the standard unexpected-error envelope
- **AND** it does not return windows, a partial curve, or a cumulative result

#### Scenario: Non-contiguous windows preserve complete detail
- **WHEN** a valid successful evaluation has an official-session gap or overlap between ordered OOS windows
- **THEN** the API returns the complete Walk-forward detail with `stitched_oos.status = unavailable_non_contiguous_windows`
- **AND** cumulative values are null and points are empty

### Requirement: Walk-forward API is read-only
The HTTP service SHALL expose `GET /api/walk-forwards`, `GET /api/walk-forwards/{run_id}`, and bodyless `POST /api/walk-forwards/run` for this history. The POST endpoint SHALL perform server-side configuration/input preflight, atomically persist one `queued` Walk-forward parent, and return HTTP 202 with its positive `walk_forward_run_id` and `status = "queued"`; it SHALL not execute a window, create an `asyncio` background task, or wait for worker completion. A partial unique-index conflict for an active queued/running record of the configured strategy SHALL return the stable HTTP 409 operation-failed envelope without inserting another parent. The service MUST NOT add a client retry, edit, delete, claim, heartbeat, or status-mutation route.

#### Scenario: OpenAPI exposes history reads plus enqueue trigger
- **WHEN** a client inspects Walk-forward paths in OpenAPI
- **THEN** exactly three Walk-forward paths are present: the two GET history/detail paths and one POST enqueue trigger
- **AND** no retry, edit, delete, claim, heartbeat, or worker-control path is present

#### Scenario: Accepted submission is durable but not executed by API
- **WHEN** a valid client posts to `/api/walk-forwards/run`
- **THEN** the response is HTTP 202 with a positive `walk_forward_run_id` and `status = "queued"`
- **AND** the committed parent contains the resolved configuration and input provenance before any worker window starts
- **AND** the API process has not created a background Walk-forward task

#### Scenario: Concurrent submission is rejected by the database invariant
- **WHEN** two requests concurrently post to `/api/walk-forwards/run` for the same strategy
- **THEN** exactly one parent is inserted with active status
- **AND** the other response is HTTP 409 using the stable operation-failed error envelope

#### Scenario: OpenAPI exposes only history reads
- **WHEN** a client inspects the Walk-forward read surface in OpenAPI
- **THEN** exactly the two GET history/detail paths are present on the read surface and remain read-only
- **AND** no retry, edit, or delete path is present on the read surface

#### Scenario: OpenAPI exposes history reads plus run trigger
- **WHEN** a client inspects Walk-forward paths in OpenAPI
- **THEN** exactly three Walk-forward paths are present: the two GET history/detail paths and one POST run-trigger path
- **AND** no retry, edit, delete, claim, heartbeat, or worker-control path is present
