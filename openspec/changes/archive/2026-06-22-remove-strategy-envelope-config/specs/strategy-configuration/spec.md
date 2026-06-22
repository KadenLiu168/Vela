## ADDED Requirements

### Requirement: Strategy configuration loader error reporting
The system SHALL wrap strategy configuration file read, YAML parse, and schema validation failures in a project-level `ConfigError`.

#### Scenario: Strategy validation error includes path and field
- **WHEN** a strategy configuration file fails schema validation while loading through the strategy config loader
- **THEN** the raised `ConfigError` message includes the strategy configuration file path and the failing field path

#### Scenario: Strategy YAML parse error includes path
- **WHEN** a strategy configuration file cannot be parsed as YAML
- **THEN** the raised `ConfigError` message includes the strategy configuration file path and parse failure context

#### Scenario: Strategy missing file error includes path
- **WHEN** backend code loads strategy configuration from a missing file path
- **THEN** the raised `ConfigError` message includes the missing strategy configuration file path
