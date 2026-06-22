## ADDED Requirements

### Requirement: Application configuration loading service
The system SHALL provide a public core configuration loading service that loads a strategy configuration and its referenced ETF pool configuration into one typed application configuration object.

#### Scenario: Load complete application configuration
- **WHEN** backend code loads application configuration from a valid strategy configuration path
- **THEN** the system returns a typed object containing the validated strategy configuration
- **AND** the object contains the validated ETF pool configuration referenced by the strategy configuration

#### Scenario: Resolve ETF pool from strategy universe config
- **WHEN** a strategy configuration contains a relative `universe_config` path
- **THEN** the loading service resolves that path and loads the referenced ETF pool configuration

#### Scenario: Missing referenced ETF pool is reported clearly
- **WHEN** backend code loads application configuration whose strategy configuration references a missing ETF pool file
- **THEN** the system raises a project-level `ConfigError`
- **AND** the error message includes the missing ETF pool configuration path

#### Scenario: Invalid referenced ETF pool is reported clearly
- **WHEN** backend code loads application configuration whose referenced ETF pool file fails schema validation
- **THEN** the system raises a project-level `ConfigError`
- **AND** the error message includes the ETF pool configuration path and failing field path
