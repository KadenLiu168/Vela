## ADDED Requirements

### Requirement: Backtest responses expose persisted expanded risk metrics
Successful backtest-run and backtest-detail responses SHALL expose strategy Sortino, Calmar and longest drawdown duration fields. Every benchmark entry SHALL expose its own Sortino, Calmar and duration fields plus strategy-relative Tracking Error and Information Ratio. Decimal values SHALL remain strings, duration counts SHALL be integers, dates SHALL be ISO dates, and unavailable values SHALL be null.

#### Scenario: New detail exposes strategy and dual-benchmark metrics
- **WHEN** a client reads a newly completed benchmark-enabled backtest
- **THEN** the strategy response contains the persisted Sortino, Calmar and duration fields
- **AND** each fixed benchmark contains its persisted downside, duration, TE and IR fields

#### Scenario: Legacy detail returns explicit nulls
- **WHEN** a client reads a run created before expanded metric support
- **THEN** the response succeeds
- **AND** all expanded strategy and benchmark fields are null rather than dynamically recalculated
