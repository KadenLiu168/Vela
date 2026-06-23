## ADDED Requirements

### Requirement: Export latest strategy signal report
The system SHALL provide a core report export helper that formats the latest successful persisted strategy signal as human-readable text.

#### Scenario: Export latest successful signal report
- **WHEN** backend code exports a report for a config version with at least one successful persisted strategy signal
- **THEN** the report includes the signal date, config version, signal id, generated timestamp, result, and fallback status
- **AND** the report includes each selected ETF with exchange, symbol, target weight, rank, score, and fallback status

#### Scenario: Export date-constrained signal report
- **WHEN** backend code exports a report for a config version and signal date
- **THEN** the report uses the latest successful persisted signal for that exact config version and signal date

#### Scenario: Report fallback signal
- **WHEN** backend code exports a report for a persisted defensive fallback signal
- **THEN** the report marks fallback status as active
- **AND** the fallback position shows no rank or score value

#### Scenario: No successful signal exists
- **WHEN** backend code exports a report and no matching successful strategy signal exists
- **THEN** the helper reports that no latest successful strategy signal is available
