# strategy-configuration Specification

## Purpose
Define versioned strategy configuration files and validation behavior used by ETF rotation signal generation and historical backtesting.
## Requirements
### Requirement: Versioned strategy configuration file
The system SHALL provide a checked-in `config/strategy_v1.yaml` file for the initial ETF rotation strategy configuration.

#### Scenario: Strategy v1 config exists
- **WHEN** backend code or a developer reads `config/strategy_v1.yaml`
- **THEN** the file exists in the repository
- **AND** the file identifies the strategy configuration version as `v1`

#### Scenario: Strategy v1 config defines required parameter groups
- **WHEN** backend code parses `config/strategy_v1.yaml`
- **THEN** the configuration includes momentum window parameters
- **AND** the configuration includes score weight parameters
- **AND** the configuration includes Top N selection parameters
- **AND** the configuration includes a defensive asset
- **AND** the configuration includes transaction cost parameters

### Requirement: Strategy configuration schema validation
The system SHALL define a Pydantic schema that validates the strategy configuration contract.

#### Scenario: Checked-in strategy config validates
- **WHEN** backend code loads `config/strategy_v1.yaml` and validates it with the strategy configuration schema
- **THEN** validation succeeds

#### Scenario: Missing required strategy parameters are rejected
- **WHEN** backend code validates a strategy configuration missing a required parameter group
- **THEN** validation fails

#### Scenario: Invalid momentum windows are rejected
- **WHEN** backend code validates a strategy configuration with non-positive momentum window lengths
- **THEN** validation fails

#### Scenario: Invalid momentum window relationship is rejected
- **WHEN** backend code validates a strategy configuration whose short momentum window is greater than or equal to its long momentum window
- **THEN** validation fails

#### Scenario: Invalid score weights are rejected
- **WHEN** backend code validates a strategy configuration whose score weights do not form a valid scoring contract
- **THEN** validation fails

#### Scenario: Non-positive score weights are rejected
- **WHEN** backend code validates a strategy configuration whose short or long score weight is less than or equal to zero
- **THEN** validation fails

#### Scenario: Invalid Top N is rejected
- **WHEN** backend code validates a strategy configuration with `top_n` less than one
- **THEN** validation fails

#### Scenario: Invalid transaction cost is rejected
- **WHEN** backend code validates a strategy configuration with a negative transaction cost
- **THEN** validation fails

### Requirement: Defensive asset identity
The system SHALL represent the defensive asset in strategy configuration with explicit ETF identity fields.

#### Scenario: Defensive asset uses exchange and symbol
- **WHEN** backend code validates the strategy configuration defensive asset
- **THEN** the defensive asset includes an exchange value
- **AND** the defensive asset includes a symbol value

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
