## ADDED Requirements

### Requirement: Apply transaction costs to strategy equity curve
The system SHALL deduct transaction costs from strategy equity curve daily returns using the transaction cost rate defined by the strategy configuration.

#### Scenario: Initial entry cost
- **WHEN** backend code calculates an equity curve for a date after the initial curve point where holdings enter from an empty prior snapshot
- **THEN** the daily return subtracts turnover equal to the sum of current target weights multiplied by `transaction_cost_bps / 10000`

#### Scenario: Rebalance cost
- **WHEN** backend code calculates an equity curve for a date whose target holdings differ from the prior trading date
- **THEN** the daily return subtracts turnover equal to the sum of absolute target weight changes multiplied by `transaction_cost_bps / 10000`

#### Scenario: Zero transaction cost
- **WHEN** backend code calculates an equity curve with strategy configuration transaction cost set to zero
- **THEN** the daily return is not reduced by transaction costs
