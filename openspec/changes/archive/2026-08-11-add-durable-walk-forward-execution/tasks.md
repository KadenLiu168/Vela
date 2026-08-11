## 1. Durable persistence contract

- [x] 1.1 Extend `WalkForwardRun` ORM lifecycle fields, status constraint, and indexes for queued/claimed durable execution.
- [x] 1.2 Add an Alembic SQLite migration that preserves terminal history, fails legacy unclaimed running rows, and creates the strategy-active and global-running partial unique indexes.
- [x] 1.3 Add migration tests against test-owned file-backed SQLite databases for fresh schema, historical preservation, legacy-running cutover, and index enforcement.
- [x] 1.4 Implement core enqueue, conditional claim, heartbeat, terminal transition, and lost-claim persistence helpers with injected clock/lease constants.

## 2. Claim-owned Walk-forward execution

- [x] 2.1 Refactor `WalkForwardRunner` to execute an existing claimed parent from persisted configuration/base-strategy snapshots instead of creating a second parent.
- [x] 2.2 Revalidate queued input provenance before source output and fail closed on checksum/manifest drift.
- [x] 2.3 Fence success and failure publication by claim token, preserving one transaction for OOS artifacts, windows, evidence, and final parent status.
- [x] 2.4 Add core tests for concurrent enqueue/claim, stale-token rejection, expired-lease recovery, retry exhaustion, drift failure, and rollback of fenced/failed artifacts.

## 3. Worker and CLI entrypoints

- [x] 3.1 Add `vela walk-forward-worker` with long-running and `--once` modes, unique worker identity, bounded polling, and safe SQLite lock handling.
- [x] 3.2 Route `vela walk-forward` through enqueue/claim while preserving its successful report, id output, `--output`, and non-zero failure behavior.
- [x] 3.3 Add CLI integration tests using temporary SQLite databases for worker once-mode, API-independent recovery, SQLite-only rejection, and CLI contention behavior.

## 4. API and web lifecycle surface

- [x] 4.1 Replace API-process background execution with enqueue-only `POST /api/walk-forwards/run`; map database active-job conflicts to the established 409 envelope.
- [x] 4.2 Extend typed Walk-forward list/detail schemas and queries for queued/running lifecycle metadata without exposing worker identity or claim token.
- [x] 4.3 Add API contract tests proving a POST commits only a queued parent, never creates an asyncio task, and remains race-safe across real SQLite sessions.
- [x] 4.4 Update the Walk-forward list UI/API client to render queued and running states, discover active work after reload, poll only while visible, and handle terminal failure/conflict.
- [x] 4.5 Add frontend interaction and rendered viewport tests for queued/running/success/failed trigger states without regressions to existing Walk-forward detail evidence.

## 5. Verification and delivery readiness

- [x] 5.1 Run targeted migration, core, CLI, API, and web tests using only test-owned databases; verify no test targets repository `vela.db`.
- [x] 5.2 Run `openspec validate add-durable-walk-forward-execution --strict` and repair all Change-local validation findings.
- [x] 5.3 Run the complete Python and Web CI-equivalent gates after the final stable revision, then inspect the diff for scope and migration safety.
