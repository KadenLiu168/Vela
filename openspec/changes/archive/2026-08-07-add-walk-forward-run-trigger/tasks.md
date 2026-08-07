## 1. Data model and migration

- [x] 1.1 Add `status` (`String(16), nullable=False, default="success"`) and `error_message` (`Text, nullable=True`) columns to `WalkForwardRun` in `packages/core/src/vela_core/models/walk_forward.py`, with a CHECK constraint `status IN ('running','success','failed')`; change `finished_at` from `nullable=False` to `nullable=True`
- [x] 1.2 Create Alembic migration `alembic/versions/<rev>_add_walk_forward_run_status.py` that adds the two columns, alters `finished_at` to nullable, and backfills every existing `WalkForwardRun` row with `status='success'`, `error_message=NULL`; downgrade reverses the column changes without touching existing rows
- [x] 1.3 Run migration against a `/tmp` copy of `vela.db` via `--database-url` to verify upgrade backfill and downgrade round-trip; do NOT apply to the default `vela.db`

## 2. Runner two-phase persistence refactor

- [x] 2.1 In `packages/core/src/vela_core/walk_forward/persistence.py`, add `persist_walk_forward_running(session, ...) -> int` (inserts parent with `status='running'`, placeholder `evidence_json={}`, `window_count=0`, null `finished_at`, commits, returns id) and `update_walk_forward_status(session, run_id, status, *, error_message=None, finished_at, window_count=None, evidence_json=None)` helpers
- [x] 2.2 Refactor `WalkForwardRunner.run()` in `packages/core/src/vela_core/walk_forward/runner.py` to: (a) call `persist_walk_forward_running` after `prepare_walk_forward_inputs` to commit a running row and obtain `run_id`; (b) wrap window execution in try/except; (c) on success call `update_walk_forward_status('success', ...)` + persist children in one final commit; (d) on exception call `update_walk_forward_status('failed', error_message=str(exc), finished_at=now)` commit then re-raise
- [x] 2.3 Preserve the existing `_memory_snapshot` backup semantics and the SQLite-only guard; ensure OOS/signal/curve/benchmark rows added after the running-row commit are still rolled back by the caller-managed transaction on failure while the parent `failed` row remains
- [x] 2.4 Add unit tests in `packages/core/tests/` covering: running row persisted before first window; success path updates to success with windows; failure path updates to failed with error_message and no children; preflight failure before running-row insert leaves no parent row

## 3. Application configuration injection

- [x] 3.1 Add `walk_forward_config_path: Path` (default `config/walk_forward_v1.yaml`) to `AppConfig` in the `application-configuration` capability surface, validated at lifespan startup like the existing strategy config path; document that the API run-trigger endpoint reads this path and MUST NOT accept a client-supplied path
- [x] 3.2 Add a unit test confirming lifespan startup rejects a missing or invalid `walk_forward_config_path`

## 4. API run-trigger endpoint and response schemas

- [x] 4.1 Add `POST /api/walk-forwards/run` endpoint in `apps/api/src/vela_api/walk_forward_router.py` as `async def` using `asyncio.to_thread` to call `WalkForwardRunner.run()` off the event loop; load config path from `AppConfig`; return HTTP 202 with `{ "walk_forward_run_id": <int> }`
- [x] 4.2 Implement concurrent-run guard: reject with HTTP 409 `operation_failed` when a current-strategy `WalkForwardRun` with `status='running'` and `started_at` within the last hour already exists
- [x] 4.3 Map expected runner failures (missing config, empty calendar, insufficient prices, no scorable combinations) to existing `apps/api/src/vela_api/errors.py` typed domain mapping with `validation` or `operation_failed` category and HTTP 400; unexpected exceptions use the standard unexpected-error contract (HTTP 500); ensure no `running` row is left persisted when the runner raises before the running-row insert
- [x] 4.4 Add `status` and `error_message` fields to `WalkForwardRunResponse`, `WalkForwardDetailResponse`, and the list summary schema in `apps/api/src/vela_api/schemas.py`; update `walk_forward_router.py` serializers to include them; ensure `running` records (null `finished_at`) sort before completed records by `started_at DESC`
- [x] 4.5 Add API contract tests: accepted run returns 202 with positive id and a `running` row; missing market data returns 400 `operation_failed` and leaves no running row; client-supplied `configPath` query/body returns 422 `validation` and starts no run; concurrent run against non-stale running record returns 409; legacy success row backfilled by migration returns `status='success'`

## 5. CLI path sync (no behavior regression)

- [x] 5.1 Update `apps/cli/src/vela_cli/main.py` `run_walk_forward()` to call the refactored `WalkForwardRunner.run()`; CLI remains synchronous-blocking, prints `walk_forward_run_id` and report on success, exits non-zero on failure with the failed parent row remaining persisted
- [x] 5.2 Add/extend CLI tests covering: successful run prints run id and report; failure exits non-zero and leaves a `failed` parent row with `error_message`; preflight failure (e.g. nonexistent config) exits non-zero and leaves no parent row

## 6. Frontend API client and run button

- [x] 6.1 Add `runWalkForward(): Promise<{ walk_forward_run_id: number }>` to `apps/web/src/api/client.ts` calling `POST /api/walk-forwards/run` with no body and no query params; add `status` and `error_message` to `WalkForwardPageResponse`/`WalkForwardDetailResponse` types
- [x] 6.2 Add "Run walk-forward" button to `apps/web/src/pages/WalkForwardListPage.tsx`: on click call `runWalkForward()`, disable button + show running indicator, poll `GET /api/walk-forwards/{run_id}` every 5s reading `status`; on `success` navigate to `/walk-forwards/{run_id}`; on `failed` surface `error_message` and re-enable; stop polling when document hidden, resume when visible
- [x] 6.3 Handle HTTP 409 concurrent-run conflict: surface conflict error, do not issue second POST, re-enable button
- [x] 6.4 Optionally add "Run walk-forward" action to `apps/web/src/components/CommandPalette.tsx` aligned with existing Run backtest / Generate signal actions
- [x] 6.5 Add frontend component tests: click Run calls `runWalkForward`; button disabled while pending; success navigates to detail; failed surfaces `error_message` and re-enables; 409 surfaces conflict without second POST; polling pauses when document hidden

## 7. End-to-end and quality gates

- [x] 7.1 Add end-to-end test (using `tmp_path` test database with `--database-url`) with an intentionally minimal parameter space (1 combination × 1 window) that triggers `POST /api/walk-forwards/run`, polls `GET /api/walk-forwards/{id}`, and asserts `status` transitions `running` → `success` with one child window persisted
- [x] 7.2 Add end-to-end failure-path test (mocked runner or minimal space that triggers `no scorable combinations`) asserting `status` transitions `running` → `failed` with `error_message` and no children
- [x] 7.3 Run full Python gate: `uv sync --group dev`, `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, `uv run --no-sync pytest`
- [x] 7.4 Run full Web gate: `npm --prefix apps/web run lint`, `lint:css`, `typecheck`, `test`, `build`
- [x] 7.5 Run `openspec validate "add-walk-forward-run-trigger" --strict` and `openspec validate --all --strict` to confirm no spec drift; do NOT archive, commit, or push unless explicitly authorized
