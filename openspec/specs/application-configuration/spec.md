# application-configuration Specification

## Purpose
Define shared YAML configuration loading, ETF pool configuration validation, and configuration error reporting. Concrete strategy parameter schemas are defined by the `strategy-configuration` capability.
## Requirements
### Requirement: ETF pool configuration schema
The system SHALL define a Pydantic schema for YAML ETF pool configuration.

#### Scenario: Load valid ETF pool YAML
- **WHEN** backend code loads a valid ETF pool YAML file
- **THEN** the system returns a typed ETF pool configuration object containing pool identity, provider, currency, and ETF entries

#### Scenario: Preserve ETF exchange as string
- **WHEN** an ETF pool YAML file contains ETF entries with exchange codes
- **THEN** the typed ETF entries expose exchange values as strings without restricting them to a fixed enum

#### Scenario: Reject duplicate ETF in pool
- **WHEN** an ETF pool YAML file contains more than one ETF entry with the same exchange and symbol
- **THEN** the system rejects the configuration with a validation error identifying the duplicate ETF

#### Scenario: Allow same symbol on different exchanges
- **WHEN** an ETF pool YAML file contains the same symbol on different exchange values
- **THEN** the system accepts both ETF entries as distinct pool members

### Requirement: YAML configuration loading
The system SHALL provide public loader functions that load supported YAML files into typed configuration objects.

#### Scenario: Load ETF pool from path
- **WHEN** backend code calls the ETF pool config loader with a YAML file path
- **THEN** the loader reads the file and returns an ETF pool configuration object

### Requirement: Configuration error reporting
The system SHALL wrap configuration file read, YAML parse, and schema validation failures in a project-level `ConfigError`.

#### Scenario: Validation error includes path and field
- **WHEN** a YAML configuration file fails schema validation
- **THEN** the raised `ConfigError` message includes the configuration file path and the failing field path

#### Scenario: YAML parse error includes path
- **WHEN** a YAML configuration file cannot be parsed
- **THEN** the raised `ConfigError` message includes the configuration file path and parse failure context

#### Scenario: Missing file error includes path
- **WHEN** backend code loads configuration from a missing file path
- **THEN** the raised `ConfigError` message includes the missing configuration file path

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

### Requirement: ETF pool metadata synchronization source
The system SHALL allow validated ETF pool configuration to be used as the source for synchronizing local ETF metadata.

#### Scenario: Provide ETF pool entries for synchronization
- **WHEN** backend code loads application configuration from a valid strategy configuration path
- **THEN** the loaded ETF pool entries can be passed to the ETF metadata synchronization workflow without re-reading the ETF pool file separately

#### Scenario: Reject invalid synchronization source
- **WHEN** the referenced ETF pool configuration is missing or invalid
- **THEN** the existing configuration loading error handling prevents ETF metadata synchronization from running with invalid pool data

