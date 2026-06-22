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

#### Scenario: Invalid score weights are rejected
- **WHEN** backend code validates a strategy configuration whose score weights do not form a valid scoring contract
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
