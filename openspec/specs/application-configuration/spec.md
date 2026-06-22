# application-configuration Specification

## Purpose
TBD - created by archiving change define-pydantic-config-schema. Update Purpose after archive.
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

### Requirement: Strategy envelope configuration schema
The system SHALL define a conservative Pydantic schema for YAML strategy envelope configuration.

#### Scenario: Load valid strategy envelope YAML
- **WHEN** backend code loads a valid strategy envelope YAML file
- **THEN** the system returns a typed strategy envelope configuration object containing strategy name, config version, universe pool id, and parameters

#### Scenario: Preserve algorithm-neutral parameters
- **WHEN** a strategy envelope YAML file contains parameter keys for a future strategy algorithm
- **THEN** the typed strategy envelope configuration exposes those parameters without requiring algorithm-specific schema fields

### Requirement: YAML configuration loading
The system SHALL provide public loader functions that load YAML files into typed configuration objects.

#### Scenario: Load ETF pool from path
- **WHEN** backend code calls the ETF pool config loader with a YAML file path
- **THEN** the loader reads the file and returns an ETF pool configuration object

#### Scenario: Load strategy envelope from path
- **WHEN** backend code calls the strategy envelope config loader with a YAML file path
- **THEN** the loader reads the file and returns a strategy envelope configuration object

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
