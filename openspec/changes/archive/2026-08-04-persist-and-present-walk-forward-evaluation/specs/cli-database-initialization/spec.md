## ADDED Requirements

### Requirement: Walk-forward CLI identifies persisted successful evaluation
After a successful caller-managed commit, `vela walk-forward` SHALL print the persisted Walk-forward run id together with the existing terminal evidence report and SHALL continue to write the same evidence report when `--output` is supplied. A failed execution or commit SHALL exit non-zero and MUST NOT print a persisted run id. A runner-flushed id MUST NOT be described as persisted before `managed_session` exits successfully.

#### Scenario: Successful CLI prints history id
- **WHEN** all Walk-forward windows complete and the managed transaction commits
- **THEN** stdout includes `Walk-forward run id: <id>` and the evidence report

#### Scenario: Output file behavior is preserved
- **WHEN** a successful command supplies `--output`
- **THEN** the report file is written as before
- **AND** stdout also identifies the persisted run id

#### Scenario: Failed CLI has no persisted id
- **WHEN** execution fails and the managed transaction rolls back
- **THEN** the command exits non-zero
- **AND** does not claim that a Walk-forward run was persisted

#### Scenario: Commit failure has no persisted id
- **WHEN** the runner returns a flushed parent id but the managed commit fails
- **THEN** the command exits non-zero
- **AND** stdout does not contain `Walk-forward run id:`
