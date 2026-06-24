## ADDED Requirements

### Requirement: Calculate Sharpe ratio from strategy metrics
The system SHALL calculate Sharpe ratio from annualized return, annualized volatility, and configured annual risk-free rate.

#### Scenario: Typical positive Sharpe ratio
- **WHEN** backend code calculates Sharpe ratio with annualized return greater than risk-free rate and positive volatility
- **THEN** the system returns `(annualized_return - risk_free_rate) / volatility`
- **AND** the result is quantized to six decimal places

#### Scenario: Negative excess return
- **WHEN** backend code calculates Sharpe ratio with annualized return less than risk-free rate and positive volatility
- **THEN** the system returns a negative Sharpe ratio

#### Scenario: Unavailable input metric
- **WHEN** backend code calculates Sharpe ratio without an annualized return or without volatility
- **THEN** the system returns no Sharpe ratio value

#### Scenario: Zero volatility
- **WHEN** backend code calculates Sharpe ratio with zero volatility
- **THEN** the system returns no Sharpe ratio value
