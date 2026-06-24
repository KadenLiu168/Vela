## ADDED Requirements

### Requirement: Test strategy equity curve calculation
The system SHALL include regression tests for strategy equity curve calculation covering held-position returns, initial net value, daily net values, and rebalance effects.

#### Scenario: Verify initial and daily net values from held-position returns
- **WHEN** the strategy equity curve is calculated for multiple trading dates with held ETFs that have complete strategy prices
- **THEN** the tests verify the first curve point has net value `1.000000`
- **AND** the tests verify each following daily net value equals the prior net value multiplied by one plus the weighted held-position return
- **AND** the tests verify each following daily return value

#### Scenario: Verify rebalance impact on the equity curve
- **WHEN** the strategy equity curve is calculated across a date where a newer successful strategy signal changes target holdings
- **THEN** the tests verify the date after the rebalance uses the newer target holdings for its weighted daily return
- **AND** the tests verify the resulting net value reflects that rebalance-driven return
