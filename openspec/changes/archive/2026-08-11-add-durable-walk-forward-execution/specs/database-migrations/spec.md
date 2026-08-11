## ADDED Requirements

### Requirement: SQLite durable Walk-forward execution migration
The Alembic revision for durable Walk-forward execution SHALL expand `walk_forward_run.status` to `queued`, `running`, `success`, and `failed`; add nullable `claimed_at`, `heartbeat_at`, `lease_expires_at`, `worker_id`, and `claim_token`; add non-negative `attempt_count`; and create SQLite partial unique indexes that allow at most one queued/running row per strategy and at most one running row per SQLite database. It SHALL preserve completed/failed history and all child/OOS/source owners. It SHALL convert an existing unclaimed running row to a terminal failed row with a bounded migration-interruption message rather than silently resuming it.

#### Scenario: Fresh SQLite database receives durable constraints
- **WHEN** Alembic upgrades an empty SQLite database to head
- **THEN** `walk_forward_run` has every durable lifecycle column and status constraint
- **AND** attempts to create duplicate active records for one strategy or two running records in one SQLite database violate the corresponding unique index

#### Scenario: Upgrade preserves historical owners and closes legacy running work
- **WHEN** Alembic upgrades a SQLite database containing terminal history and an unclaimed running parent
- **THEN** existing terminal parents, children, OOS rows, signals, curves, and benchmarks remain unchanged
- **AND** the unclaimed running parent becomes terminal failed without launching a worker or creating artifacts
