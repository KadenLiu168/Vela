# strategy-configuration Specification

## Purpose
Define versioned strategy configuration files and validation behavior used by ETF rotation signal generation and historical backtesting.
## Requirements
### Requirement: Versioned strategy configuration file
The system SHALL provide a checked-in `config/strategy_v1.yaml` file for the initial ETF rotation strategy configuration.

#### Scenario: Strategy v1 config defines required parameter groups
- **WHEN** backend code parses `config/strategy_v1.yaml`
- **THEN** the configuration includes momentum window parameters
- **AND** the configuration includes score weight parameters
- **AND** the configuration includes trend filter parameters
- **AND** the configuration includes Top N selection parameters
- **AND** the configuration includes one or more defensive assets (a `defense.assets` list)
- **AND** the configuration includes transaction cost parameters
- **AND** the configuration includes performance metric parameters

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

#### Scenario: Invalid trend filter is rejected
- **WHEN** backend code validates a strategy configuration whose trend filter uses an unsupported moving-average window or price relation
- **THEN** validation fails

#### Scenario: Invalid Top N is rejected
- **WHEN** backend code validates a strategy configuration with `top_n` less than one
- **THEN** validation fails

#### Scenario: Invalid transaction cost is rejected
- **WHEN** backend code validates a strategy configuration with a negative transaction cost
- **THEN** validation fails

#### Scenario: Invalid risk-free rate is rejected
- **WHEN** backend code validates a strategy configuration with a negative performance `risk_free_rate`
- **THEN** validation fails

#### Scenario: Strategy schema validation exposes assertable failure details
- **WHEN** backend tests validate invalid strategy configuration values directly with the strategy configuration schema
- **THEN** validation fails with assertable details identifying the failing field or project-owned validation message

### Requirement: Defensive asset identity
The system SHALL represent one or more defensive assets in strategy configuration, each with explicit ETF identity fields.

#### Scenario: Defensive asset uses exchange and symbol
- **WHEN** backend code validates the strategy configuration defensive assets
- **THEN** each defensive asset includes an exchange value
- **AND** each defensive asset includes a symbol value

#### Scenario: At least one defensive asset is required
- **WHEN** backend code validates a strategy configuration with an empty `defense.assets` list
- **THEN** validation fails

#### Scenario: Duplicate defensive assets are rejected
- **WHEN** backend code validates a strategy configuration whose `defense.assets` list contains two entries with the same exchange and symbol
- **THEN** validation fails

#### Scenario: Defensive asset exists in active ETF universe
- **WHEN** backend code loads a strategy configuration with one or more defensive assets
- **THEN** each defensive asset exists in the ETF pool referenced by `universe_config`
- **AND** each matching ETF pool entry is active

#### Scenario: Defensive asset outside active ETF universe is rejected
- **WHEN** backend code loads a strategy configuration whose defensive asset is missing from the referenced ETF pool or is inactive
- **THEN** validation fails with a project-level configuration error identifying `defense.assets[i]`

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

### Requirement: Rebalance frequency parameter
The system SHALL define a rebalance frequency parameter group in the strategy configuration that selects the rebalance date generation frequency.

#### Scenario: Strategy v1 config defines rebalance parameter group
- **WHEN** backend code parses `config/strategy_v1.yaml`
- **THEN** the configuration includes a rebalance parameter group
- **AND** the rebalance parameter group includes a `frequency` field

#### Scenario: Rebalance frequency accepts weekly value
- **WHEN** backend code validates a strategy configuration with `rebalance.frequency` set to `"weekly"`
- **THEN** validation succeeds

#### Scenario: Rebalance frequency accepts monthly value
- **WHEN** backend code validates a strategy configuration with `rebalance.frequency` set to `"monthly"`
- **THEN** validation succeeds

#### Scenario: Rebalance frequency rejects unsupported value
- **WHEN** backend code validates a strategy configuration with `rebalance.frequency` set to any value other than `"weekly"` or `"monthly"`
- **THEN** validation fails

#### Scenario: Rebalance frequency defaults to weekly when omitted
- **WHEN** backend code loads a strategy configuration that omits the rebalance parameter group
- **THEN** the loaded configuration uses `weekly` as the rebalance frequency
- **AND** the loaded configuration is otherwise valid

### Requirement: Trend filter configuration accepted values
The strategy configuration schema SHALL accept `trend_filter.moving_average_days` values from the closed set `{60, 120, 250}` and `trend_filter.price_relation` values from the closed set `{above, below}`. Any value outside these sets SHALL be rejected at load time.

#### Scenario: 120-day above trend filter is accepted
- **WHEN** backend code validates a strategy configuration with `trend_filter.moving_average_days` set to `120` and `trend_filter.price_relation` set to `above`
- **THEN** validation succeeds

#### Scenario: 60-day below trend filter is accepted
- **WHEN** backend code validates a strategy configuration with `trend_filter.moving_average_days` set to `60` and `trend_filter.price_relation` set to `below`
- **THEN** validation succeeds

#### Scenario: 250-day above trend filter is accepted
- **WHEN** backend code validates a strategy configuration with `trend_filter.moving_average_days` set to `250` and `trend_filter.price_relation` set to `above`
- **THEN** validation succeeds

#### Scenario: Unsupported moving average window is rejected
- **WHEN** backend code validates a strategy configuration with `trend_filter.moving_average_days` set to a value other than `60`, `120`, or `250` (for example `30`)
- **THEN** validation fails

#### Scenario: Unsupported price relation is rejected
- **WHEN** backend code validates a strategy configuration with `trend_filter.price_relation` set to a value other than `above` or `below` (for example `near`)
- **THEN** validation fails

