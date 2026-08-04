## ADDED Requirements

### Requirement: Calculate downside and drawdown-duration metrics from strategy equity
The strategy equity metric layer SHALL calculate Sortino using the configured risk-free rate, Calmar using the existing calendar-time annualized return and negative maximum drawdown, and longest drawdown duration from the ordered official-session points according to `active-and-downside-risk-metrics`.

#### Scenario: One curve produces consistent expanded metrics
- **WHEN** a valid strategy curve has sufficient effective returns, non-zero downside deviation and a non-zero maximum drawdown
- **THEN** the metric layer returns Sortino, Calmar and longest-duration fields from that same curve
- **AND** does not change total return, CAGR, maximum drawdown, volatility or Sharpe

#### Scenario: Flat curve preserves distinct null and zero values
- **WHEN** a valid strategy curve never goes underwater and has zero downside deviation
- **THEN** longest drawdown duration is zero
- **AND** Sortino and Calmar are null
