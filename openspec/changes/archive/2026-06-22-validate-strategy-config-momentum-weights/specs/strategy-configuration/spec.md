## MODIFIED Requirements

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

#### Scenario: Defensive asset exists in active ETF universe
- **WHEN** backend code loads a strategy configuration with a defensive asset
- **THEN** the defensive asset exists in the ETF pool referenced by `universe_config`
- **AND** the matching ETF pool entry is active

#### Scenario: Defensive asset outside active ETF universe is rejected
- **WHEN** backend code loads a strategy configuration whose defensive asset is missing from the referenced ETF pool or is inactive
- **THEN** validation fails with a project-level configuration error identifying `defense.asset`
