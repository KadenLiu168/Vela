## MODIFIED Requirements

### Requirement: Latest successful strategy signal query
The system SHALL provide a core query helper that returns the latest successful strategy signal
for a `strategy_id`, `signal_date`, and `config_version` with its positions available.

#### Scenario: Latest successful signal exists
- **WHEN** backend code queries for a strategy id, date, and config version that have multiple
  successful strategy signal runs
- **THEN** the helper returns the matching successful run with the newest `generated_at` timestamp
  and id tie-breaker
- **AND** it ignores runs belonging to other strategies or config versions

#### Scenario: Latest successful signal ignores non-success rows
- **WHEN** backend code queries for a strategy id, date, and config version where a newer
  non-success run exists after an older successful run
- **THEN** the helper returns the older matching successful run

#### Scenario: Latest successful signal does not exist
- **WHEN** backend code queries for a strategy id, date, and config version that have no matching
  successful strategy signal run
- **THEN** the helper returns no signal
