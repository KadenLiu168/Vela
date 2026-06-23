## ADDED Requirements

### Requirement: Calculate maximum drawdown from strategy equity curve
The system SHALL calculate maximum drawdown from strategy equity curve points using each point's net value and trade date.

#### Scenario: Typical drawdown curve
- **WHEN** backend code calculates maximum drawdown for an equity curve that rises to a peak and then falls to a lower trough
- **THEN** the system returns the lowest drawdown value equal to `trough_net_value / peak_net_value - 1`
- **AND** the system returns the peak and trough dates that define that maximum drawdown interval

#### Scenario: No drawdown
- **WHEN** backend code calculates maximum drawdown for an empty, flat, or all-rising equity curve
- **THEN** the system returns maximum drawdown `0.000000`
- **AND** the system returns no peak or trough date interval
