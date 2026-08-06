## ADDED Requirements

### Requirement: Fixed benchmark curves expose matching stability series
Backtest Detail stability derivation SHALL process each persisted fixed benchmark curve using the same validation, adjacent-net-value return reconstruction, 63-session rolling, calendar grouping, requested-scope partial flag, risk-free-rate input, precision, and ordering rules as the strategy. Benchmark identity and result ownership SHALL remain explicit.

#### Scenario: Strategy and benchmark use identical derivation rules
- **WHEN** strategy and one benchmark have identical persisted curve values and dates
- **THEN** their rolling and calendar stability values are identical
- **AND** remain attached to their separate entity identities

#### Scenario: Legacy run has no fabricated benchmark series
- **WHEN** a legacy backtest has no benchmark children
- **THEN** strategy stability remains available when its curve is valid
- **AND** the benchmark stability collection is empty
