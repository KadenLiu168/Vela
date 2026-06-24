## ADDED Requirements

### Requirement: Test transaction cost calculation
The system SHALL include regression tests for strategy equity curve transaction cost calculation across turnover amounts, configured cost rates, and net value impact.

#### Scenario: Different turnover amounts
- **WHEN** backend tests calculate strategy equity curves for rebalances with different absolute target weight changes
- **THEN** the tests verify each daily return subtracts `turnover * transaction_cost_bps / 10000`

#### Scenario: Different transaction cost rates
- **WHEN** backend tests calculate strategy equity curves for the same turnover with different configured transaction cost basis points
- **THEN** the tests verify the higher cost rate produces the larger daily return deduction

#### Scenario: Net value impact
- **WHEN** backend tests calculate a strategy equity curve with transaction costs and non-zero market returns
- **THEN** the tests verify each affected net value compounds the return after transaction cost deduction
