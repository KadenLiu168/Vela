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

