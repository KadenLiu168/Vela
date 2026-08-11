## Why

`POST /api/walk-forwards/run` currently starts `WalkForwardRunner.complete()` in an API-process background thread. A deployment, crash, or Uvicorn restart can therefore abandon an execution while its persisted parent remains `running`. Its concurrent-run guard also uses a non-atomic read followed by an insert, so concurrent requests can create more than one active execution for a strategy.

Walk-forward results are research evidence. Their execution lifecycle must be durable, singular, and auditable before further performance work is trusted.

## What Changes

- Turn the existing `WalkForwardRun` parent into the durable Walk-forward job ledger, adding `queued` state, claim ownership, heartbeat/lease timestamps, attempt counting, and a fencing token.
- **BREAKING** Replace in-process API background execution with an enqueue-only `POST /api/walk-forwards/run` response. A separately supervised `vela walk-forward-worker` claims and runs durable jobs.
- Enforce one active (`queued` or `running`) Walk-forward job per strategy in SQLite with a partial unique index; map the index conflict to the existing HTTP 409 contract.
- Make all worker heartbeat, terminal status, and result-publication transitions conditional on the active claim token so a stale worker cannot publish or overwrite a newer attempt.
- Recover expired claims by retrying the complete execution from the persisted configuration/input provenance; cap repeated lost-worker retries and record a terminal failure rather than leave an indefinite `running` row.
- Route the synchronous CLI execution path through the same enqueue/claim protocol so it cannot bypass the database concurrency invariant.
- Preserve complete successful-run evidence, OOS ownership, and caller-owned rollback semantics; a failed or fenced attempt must publish neither partial children nor partial OOS artifacts.

## Capabilities

### New Capabilities

- `walk-forward-execution-worker`: Defines the supervised worker's atomic claim, heartbeat, fencing, lost-worker recovery, and retry behavior.

### Modified Capabilities

- `walk-forward-evaluation-history`: Walk-forward parent lifecycle changes from a process-owned `running` row to a durable queued/leased execution record.
- `walk-forward-runner`: The runner must execute only under a valid durable claim and atomically publish only a claim-owned terminal result.
- `http-api-service`: The run trigger becomes an enqueue-only API with durable lifecycle fields and atomic active-run rejection.
- `cli-database-initialization`: The Walk-forward CLI and the new worker command share the durable execution protocol.
- `database-migrations`: SQLite migrations add the durable execution columns, constraints, and partial unique index while safely handling legacy rows.
- `web-frontend-app`: The Walk-forward trigger and polling states must distinguish queued, running, terminal success, and terminal failure without creating duplicate requests.

## Impact

- Affected core areas: `vela_core.models.walk_forward`, Walk-forward persistence/runner/query modules, Alembic migrations, and new worker orchestration code.
- Affected applications: API route/schemas/tests, CLI command surface/tests, and Walk-forward list/detail polling UI.
- No Celery, Redis, or external broker is added. Deployment must supervise exactly one worker per SQLite database; it is intentionally independent from Uvicorn's lifecycle.
- Existing `running` rows are migration-cutover records with no valid claim token; they will be terminally failed with a bounded interruption reason rather than silently resumed.
