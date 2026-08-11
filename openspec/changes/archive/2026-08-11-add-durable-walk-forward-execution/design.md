## Context

The current API persists a `WalkForwardRun(status="running")`, then creates an in-process `asyncio` task that executes the remainder of the calculation. A process restart loses that task. The concurrent-run guard performs a separate read before insertion, and the schema has no active-run uniqueness constraint. `WalkForwardRunner.complete()` deliberately keeps OOS writes and final evidence publication in one source-database transaction, so failed executions roll back their partial artifacts.

The system is a local SQLite application. It must preserve its complete successful OOS ownership/evidence contract, must never mutate the user's default database during tests, and must not add Redis, Celery, or a generic queue framework.

## Goals / Non-Goals

**Goals:**

- Make a submitted Walk-forward execution durable across API restarts and worker crashes.
- Enforce at the database layer one active submission per strategy and one SQLite write execution at a time.
- Make stale workers unable to heartbeat, fail, or publish a result after a newer claim takes ownership.
- Preserve a complete, atomic success publication or no OOS/window artifacts from the failed attempt.
- Keep the API request short after preflight and expose enough lifecycle state for the existing list/detail UI to poll safely.
- Reuse the same durable protocol for API, CLI, and worker entrypoints.

**Non-Goals:**

- Celery, Redis, a cross-project generic job framework, distributed workers, or multiple concurrent SQLite Walk-forward writers.
- Checkpointing/resuming inside an individual Walk-forward window. Recovery retries the full execution.
- User cancellation, arbitrary retry/delete HTTP endpoints, percentage progress, or a client-supplied configuration path.
- Changing financial metrics, window selection, OOS ownership, or evidence semantics.

## Decisions

### 1. `WalkForwardRun` is the durable job ledger

The existing parent remains the single public identifier and receives these lifecycle states:

```text
queued -> running -> success
                  -> failed
running (expired lease) -> running (new claim, higher attempt_count)
```

It gains `attempt_count`, `claimed_at`, `heartbeat_at`, `lease_expires_at`, `worker_id`, and opaque `claim_token`. `created_at` remains enqueue time; `started_at` remains the accepted execution timestamp for compatibility, while `claimed_at` records the current attempt's actual start. `finished_at` is populated only by terminal states.

The enqueue path validates the fixed/server-side config and captures the resolved configuration, base-strategy snapshot, provenance manifest, and checksums before inserting a `queued` parent. This preserves the existing non-null provenance contract and causes missing-data/configuration failures to remain immediate, typed HTTP errors. The worker reconstructs its runner only from the stored snapshots and must revalidate that the current preflight manifest/checksum equals the queued record before executing. A mismatch is terminal `failed`, rather than silently making one job represent different input data.

An extra `WalkForwardJob` table is rejected for P0. It would duplicate lifecycle state and require reconciliation across job completion and the atomic source-result transaction. The existing parent already identifies execution history and can be extended without a dual-commit protocol.

### 2. SQLite constraints, not a read-then-insert guard, serialize work

The migration adds two partial unique indexes:

```sql
CREATE UNIQUE INDEX uq_walk_forward_run_active_strategy
ON walk_forward_run(strategy_id)
WHERE status IN ('queued', 'running');

CREATE UNIQUE INDEX uq_walk_forward_run_sqlite_running
ON walk_forward_run((1))
WHERE status = 'running';
```

The first prevents duplicate requests for one strategy, including a request waiting in the queue. The second serializes SQLite write execution even if two worker processes are accidentally started for different strategies. Queued work for distinct strategies remains representable; only one can be claimed at a time.

`POST` inserts directly and maps the active-strategy index's `IntegrityError` to HTTP 409 after rolling back its session. It MUST NOT make correctness depend on a preceding `SELECT`. A worker may discover a candidate by query, but it claims it only through a conditional `UPDATE` in a short transaction; one affected row is the sole evidence that it owns that attempt.

### 3. A separately supervised worker performs claims and execution

Add `vela walk-forward-worker --database-url <url>` as a long-lived process, with an `--once` mode for deterministic tests and service supervision. Deploy one worker per SQLite database independently from Uvicorn. The API never calls `asyncio.create_task()` for a Walk-forward calculation.

Each worker boot receives a unique `worker_id`. It repeatedly claims the oldest eligible current record:

- `queued` records are eligible immediately.
- `running` records become eligible only when `lease_expires_at` is strictly before the worker's clock.
- a successful conditional claim writes a fresh random `claim_token`, increments `attempt_count`, records `claimed_at`/`heartbeat_at`, and sets a bounded lease.
- an expired record at the retry limit becomes terminal `failed` with a bounded `worker_lost` reason; otherwise it is retried from the start.

The initial constants are a 15-second heartbeat interval, a 120-second lease, and three total attempts. They are injected into core orchestration so tests use a frozen clock; they are not client-controlled configuration.

An API/CLI submission only enqueues. The existing synchronous `vela walk-forward` command enqueues then claims and executes its own record synchronously, retaining its terminal report/output behavior. If another active job prevents enqueue or claim, it exits non-zero without bypassing the invariant.

### 4. Claim-token fencing makes at-least-once execution safe

The worker refreshes `heartbeat_at` and `lease_expires_at` in a separate short session using `WHERE id = :id AND status = 'running' AND claim_token = :token`. The token, worker id, and raw exception details are never returned in the HTTP API.

The runner receives the claimed id/token. In its final source transaction it writes selected OOS artifacts, child windows, evidence, and performs a conditional terminal update using the same token. The update must affect exactly one row before commit. If it does not, the runner raises a lost-claim error and rolls back that transaction, so an old worker cannot publish children or change status after reclaim. On an execution error, it rolls back the work transaction first, then conditionally records `failed`; a lost claim is logged but is not allowed to overwrite the new owner.

This gives **at-least-once execution and exactly-once visible publication**. A crash can repeat CPU work, but it cannot produce two published OOS result sets for one parent.

### 5. SQLite lease handling is deliberately conservative

WAL permits API readers while `complete()` owns its long source transaction, but SQLite still permits only one writer. A heartbeat update can therefore be blocked during the long OOS write transaction. Lease expiry is never interpreted by a GET endpoint as permission to kill a worker or report a definite failure; only the worker's conditional claim transition changes ownership.

If an old worker holds the source write transaction, a competing claim is blocked or loses its conditional update until the owner commits or the connection dies. If the old process dies, SQLite rolls back/releases its transaction and a later worker can claim the expired record. Fencing protects the small interval in which stale CPU-only work continues after a takeover. This preserves correctness without weakening the runner's all-or-nothing source transaction.

### 6. API and UI expose lifecycle, not worker internals

`POST /api/walk-forwards/run` remains bodyless and returns 202 only after the queued row commits. Its response includes the existing positive `walk_forward_run_id` and `status="queued"`. `GET` summary/detail responses expose `queued|running|success|failed`, `attempt_count`, `claimed_at`, `heartbeat_at`, and `lease_expires_at`; they never expose `claim_token` or `worker_id`.

The list keeps active records before terminal history. Detail for queued/running/failed parents validates the captured metadata but does not validate placeholder evidence or fabricate windows. The frontend treats `queued` and `running` as in-progress, resumes polling after a reload/visibility change, and re-enables the trigger only at a terminal result or an HTTP conflict/error. No new user-facing retry endpoint is added.

### 7. Migration cutover is explicit

The migration expands the status check constraint, adds lifecycle columns/checks, creates the partial indexes, and backfills completed historical rows with neutral lifecycle values. It must be applied only after stopping old API/CLI processes. Any pre-existing `running` row has no fencing token and is marked terminal `failed` with a bounded migration-interruption message; it is never silently resumed.

## Risks / Trade-offs

- **[Risk] A worker can crash repeatedly.** → Retry only expired claims, record attempts, and terminally fail after three total attempts instead of looping forever.
- **[Risk] A slow SQLite write prevents heartbeats.** → Heartbeats are best-effort; only conditional claims/terminal publication control correctness, and the worker does not declare a record failed merely because a read sees an expired timestamp.
- **[Risk] A retry sees changed market inputs.** → Compare the worker preflight manifest/checksum to the queued values and fail closed on mismatch. A user submits a new job for new data.
- **[Risk] Two worker processes are misconfigured.** → The global partial `running` index allows only one SQLite execution; the worker treats the resulting uniqueness conflict as no work claimed.
- **[Trade-off] A short API request still performs preflight.** → This maintains the existing immediate validation and immutable input contract while moving the expensive parameter search/OOS execution out of the API process.
- **[Trade-off] The worker is an operational process.** → It is a small local CLI process with no broker dependency, but it must be supervised separately from the API.

## Migration Plan

1. Stop API instances, any `vela walk-forward` command, and any legacy background execution for the target database.
2. Apply the Alembic migration only to an explicitly selected database; do not run migrations against the repository's `vela.db` as validation.
3. Mark legacy unclaimed `running` rows failed, preserve historical `success`/`failed` records, and verify the partial indexes.
4. Start exactly one supervised worker for that database, then start API instances. The worker first claims queued records and only claims a legacy/recent running record when its valid lease has expired.
5. Roll back operationally by stopping the worker and ensuring no active durable record exists before downgrading. A downgrade MUST refuse or be preceded by terminally failing active records; it must not erase an active job silently.

## Open Questions

None for the initial implementation. Lease timings, retry limit, and the one-worker SQLite policy are intentionally fixed P0 constants with deterministic tests, rather than premature deployment configuration.
