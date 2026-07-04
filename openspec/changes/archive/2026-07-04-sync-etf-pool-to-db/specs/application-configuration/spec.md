## ADDED Requirements

### Requirement: ETF pool metadata synchronization source
The system SHALL allow validated ETF pool configuration to be used as the source for synchronizing local ETF metadata.

#### Scenario: Provide ETF pool entries for synchronization
- **WHEN** backend code loads application configuration from a valid strategy configuration path
- **THEN** the loaded ETF pool entries can be passed to the ETF metadata synchronization workflow without re-reading the ETF pool file separately

#### Scenario: Reject invalid synchronization source
- **WHEN** the referenced ETF pool configuration is missing or invalid
- **THEN** the existing configuration loading error handling prevents ETF metadata synchronization from running with invalid pool data
