## ADDED Requirements

### Requirement: CLI backtest reports disclose expanded metric semantics
The `run-backtest` summary and exported backtest report SHALL display persisted strategy Sortino, Calmar and longest drawdown duration. Benchmark sections SHALL additionally display their own downside/duration values and strategy-relative Tracking Error and Information Ratio. Labels SHALL disclose risk-free MAR, 252D active-risk annualization, calendar CAGR in Calmar, and null recovery for ongoing drawdowns.

#### Scenario: CLI prints expanded completed-run metrics
- **WHEN** a new benchmark-enabled backtest completes through the CLI
- **THEN** stdout identifies the expanded strategy metrics and both benchmark-relative TE/IR values with semantic labels

#### Scenario: Export prints ongoing duration
- **WHEN** an exported run's longest drawdown has no recovery date
- **THEN** the report prints its duration, peak and trough
- **AND** identifies recovery as ongoing rather than fabricating a date

#### Scenario: Legacy values remain visible as unavailable
- **WHEN** an exported legacy run has null expanded fields
- **THEN** the report renders them as unavailable without recomputation
