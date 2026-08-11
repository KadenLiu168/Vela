## MODIFIED Requirements

### Requirement: Walk-forward CLI identifies persisted successful evaluation
After a successful durable claim and caller-managed publication commit, `vela walk-forward` SHALL print the persisted Walk-forward run id together with the existing terminal evidence report and SHALL continue to write the same evidence report when `--output` is supplied. The command SHALL use the same enqueue/claim protocol as the API worker path. A failed enqueue, claim, execution, lost claim, or publication commit SHALL exit non-zero and MUST NOT print a persisted successful run id.

#### Scenario: Successful CLI prints history id
- **WHEN** all Walk-forward windows complete under the CLI's durable claim and the publication transaction commits
- **THEN** stdout includes `Walk-forward run id: <id>` and the evidence report

#### Scenario: Output file behavior is preserved
- **WHEN** a successful command supplies `--output`
- **THEN** the report file is written as before
- **AND** stdout also identifies the persisted run id

## ADDED Requirements

### Requirement: CLI starts a durable Walk-forward worker
The system SHALL expose `vela walk-forward-worker --database-url <url>` for a supervised process that claims and executes durable Walk-forward records for one SQLite database. It SHALL support `--once` to perform at most one claim/execution cycle for deterministic tests and service managers. The worker SHALL not accept a client-provided config path and SHALL report a clear error for a non-SQLite database URL.

#### Scenario: Worker processes one queued record in once mode
- **WHEN** an operator invokes `vela walk-forward-worker --database-url <test-url> --once` and one eligible queued record exists
- **THEN** the worker claims at most that record and exits after its terminal result or failed claim
- **AND** it does not execute a second record

#### Scenario: Worker remains available across API restart
- **WHEN** the API process restarts while the separately supervised worker remains running
- **THEN** the worker continues to claim eligible persisted records from the configured database
- **AND** no API background thread is required for execution
