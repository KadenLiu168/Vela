## ADDED Requirements

### Requirement: Test maximum drawdown calculation
The system SHALL include regression tests for maximum drawdown calculation across representative strategy net value curves.

#### Scenario: Rising curve has no drawdown
- **WHEN** backend tests calculate maximum drawdown for an all-rising strategy equity curve
- **THEN** the tests verify maximum drawdown is `0.000000`
- **AND** the tests verify no peak or trough date interval is returned

#### Scenario: Falling curve records peak-to-trough loss
- **WHEN** backend tests calculate maximum drawdown for a strategy equity curve that falls from its initial peak
- **THEN** the tests verify the maximum drawdown value equals `trough_net_value / peak_net_value - 1`
- **AND** the tests verify the peak date is the initial peak date
- **AND** the tests verify the trough date is the lowest net value date

#### Scenario: Recovery after drawdown preserves deepest interval
- **WHEN** backend tests calculate maximum drawdown for a strategy equity curve that falls and later recovers without exceeding the prior peak
- **THEN** the tests verify the maximum drawdown remains the deepest peak-to-trough loss
- **AND** the tests verify the recovery point does not replace the trough date
