## ADDED Requirements

### Requirement: Worker claims durable Walk-forward executions atomically
The system SHALL provide a separately supervised Walk-forward worker that claims persisted `WalkForwardRun` records from the configured SQLite database. A claim SHALL be a short conditional database update, SHALL assign a fresh opaque `claim_token` and worker identity, SHALL increment `attempt_count`, and SHALL set `status = "running"`, `claimed_at`, `heartbeat_at`, and `lease_expires_at`. A worker SHALL claim a `queued` record immediately and SHALL reclaim a `running` record only when its lease is strictly expired. The worker SHALL process at most one claimed record at a time and SHALL not use an in-process FastAPI background task as a worker.

#### Scenario: Concurrent workers claim only one queued record
- **WHEN** two workers attempt to claim the same queued Walk-forward record concurrently
- **THEN** exactly one conditional claim update succeeds and owns a fresh claim token
- **AND** the other worker executes no Walk-forward window for that record

#### Scenario: A worker instance identifies its claim
- **WHEN** a worker claims a queued Walk-forward record
- **THEN** the record stores its attempt count, claimed timestamp, heartbeat timestamp, lease expiry, and non-empty worker identity
- **AND** the claim token is not exposed in any HTTP response

### Requirement: Worker heartbeats and terminal publication are fenced
While it owns a claim, the worker SHALL refresh its heartbeat and lease only with the matching record id, `status = "running"`, and claim token. It SHALL publish `success` or `failed` only with that same conditional ownership check. The final success transaction SHALL include all selected OOS/source artifacts, ordered child windows, evidence, and the conditional terminal update. If any ownership check affects no row, the worker SHALL treat the claim as lost, roll back its uncommitted source artifacts, and SHALL NOT overwrite the new claim's status.

#### Scenario: A stale worker cannot publish after reclaim
- **WHEN** an expired running record is reclaimed with a new token while the former worker is still computing
- **THEN** the former worker cannot refresh the heartbeat or set a terminal status
- **AND** its attempted result publication rolls back all uncommitted OOS and child artifacts

#### Scenario: Successful publication is atomic
- **WHEN** a valid claimed execution completes every window and evidence validation
- **THEN** its OOS artifacts, ordered children, final evidence, and `status = "success"` commit together
- **AND** no separately committed partial result is visible

### Requirement: Expired worker claims recover deterministically
The worker SHALL scan for queued and expired running records at startup and while idle. It SHALL retry an expired record from the beginning using its persisted configuration/base-strategy snapshots and SHALL revalidate the current preflight input manifest and checksum against the queued values before source output. A mismatch, retry-limit exhaustion, or expected execution failure SHALL produce a bounded terminal `failed` record; it SHALL not leave the parent indefinitely running. The initial retry limit SHALL be three total attempts, the heartbeat interval 15 seconds, and the lease duration 120 seconds.

#### Scenario: A crash is retried after its lease expires
- **WHEN** a worker process dies after claiming a record and before a terminal transition
- **THEN** a later worker claims the expired record with a different token and higher attempt count
- **AND** it restarts the complete Walk-forward execution rather than fabricating a mid-window resume

#### Scenario: Changed inputs fail closed during recovery
- **WHEN** a reclaimed record's current preflight manifest or checksum differs from the queued record
- **THEN** the worker marks that record failed with a bounded input-drift reason
- **AND** it creates no OOS, signal, curve, benchmark, or child artifact for the retry

#### Scenario: Repeated worker loss becomes terminal
- **WHEN** a record has exhausted three total claims without a terminal result
- **THEN** the worker records `status = "failed"` with a bounded worker-lost reason
- **AND** a new user submission is no longer blocked by that record
