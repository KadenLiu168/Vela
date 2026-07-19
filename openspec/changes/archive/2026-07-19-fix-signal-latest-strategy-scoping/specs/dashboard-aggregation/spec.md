## MODIFIED Requirements

### Requirement: Dashboard latest signal summary
The dashboard aggregation service SHALL summarize the latest successful persisted strategy signal
for the exact, case-sensitive current `strategy_id` and `config_version` for first-screen review.

#### Scenario: Latest successful signal exists
- **WHEN** multiple persisted strategy signals exist
- **THEN** the latest signal summary uses the successful signal with the newest generated timestamp and id tie-breaker whose `strategy_id` and `config_version` match the current strategy config
- **AND** it ignores failed, running, and partial signals
- **AND** it ignores signals belonging to other strategies or other config versions
- **AND** it includes signal id, signal date, config version, status, result, generated timestamp, fallback status, and position count

#### Scenario: Latest successful signal does not exist
- **WHEN** persisted strategy signals exist but none have success status for the current strategy id and config version
- **THEN** the latest signal summary is null

#### Scenario: Latest signal fallback status
- **WHEN** the latest successful signal for the current strategy id and config version has a persisted position without rank and score values
- **THEN** the latest signal summary marks fallback status as active
