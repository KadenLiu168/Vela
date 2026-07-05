# strategy-signal-generation Specification

## Purpose
TBD - created by archiving change add-generate-signal-cli-command. Update Purpose after archive.
## Requirements
### Requirement: Generate strategy signal from local market data
The system SHALL generate a strategy signal for a requested signal date using the active ETFs, stored market prices, and strategy configuration available in the local database.

#### Scenario: Generate ranked strategy signal
- **WHEN** backend code generates a strategy signal for a date with enough active ETF market price history
- **THEN** the system calculates configured momentum scores for active ETFs
- **AND** the system applies the configured trend filter before ranking eligible ETFs
- **AND** the system persists selected target positions with rank, score, and target weight

#### Scenario: Apply defensive fallback during generation
- **WHEN** backend code generates a strategy signal and fewer eligible ranked ETFs exist than the configured Top N
- **THEN** the system persists the configured defensive asset as the only target position
- **AND** the defensive position has full target weight

#### Scenario: Fail when no active ETFs exist
- **WHEN** backend code generates a strategy signal and the local database has no active ETFs
- **THEN** the system persists a failed signal run
- **AND** the result includes a clear error message

#### Scenario: Fail when defensive asset is missing locally
- **WHEN** backend code generates a fallback signal and the configured defensive asset is not present as an active local ETF
- **THEN** the system persists a failed signal run
- **AND** the result includes a clear error message

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

### Requirement: Generate historical strategy signals
The system SHALL generate strategy signals for historical rebalance dates by reusing the existing single-date strategy signal generation logic, using the rebalance frequency from the loaded strategy configuration.

#### Scenario: Generate signals for historical rebalance dates with weekly frequency
- **WHEN** backend code generates historical strategy signals from a sequence of historical trading dates with `rebalance.frequency` set to `weekly`
- **THEN** the system derives weekly rebalance dates from those trading dates
- **AND** the system generates one strategy signal for each derived rebalance date
- **AND** the generated results are returned in ascending signal date order

#### Scenario: Generate signals for historical rebalance dates with monthly frequency
- **WHEN** backend code generates historical strategy signals from a sequence of historical trading dates with `rebalance.frequency` set to `monthly`
- **THEN** the system derives monthly rebalance dates from those trading dates
- **AND** the system generates one strategy signal for each derived rebalance date
- **AND** the generated results are returned in ascending signal date order

#### Scenario: Historical generation does not use future data
- **WHEN** backend code generates a historical strategy signal for a rebalance date that has later market prices available in storage
- **THEN** strategy calculations for that signal use only market data on or before that rebalance date

#### Scenario: Historical signal positions are persisted
- **WHEN** historical strategy signal generation produces target positions for a rebalance date
- **THEN** the database contains persisted strategy signal positions for that generated signal
- **AND** each persisted position includes the target weight needed by portfolio holding calculation

#### Scenario: Empty historical trading dates
- **WHEN** backend code generates historical strategy signals from an empty trading-date sequence
- **THEN** the system returns an empty result list
- **AND** no strategy signal rows are persisted

#### Scenario: Monthly frequency produces fewer signals than weekly
- **WHEN** backend code generates historical strategy signals over the same trading-date sequence with weekly frequency and then with monthly frequency
- **THEN** the number of generated monthly-frequency signals is strictly less than the number of generated weekly-frequency signals

