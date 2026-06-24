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
