## ADDED Requirements

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
