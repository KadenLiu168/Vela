## ADDED Requirements

### Requirement: Backtest benchmark persistence model
The system SHALL persist benchmark results as child records of a `BacktestRun`. Each benchmark record SHALL store a stable benchmark key, display name, the five metric fields, and ordered daily net-value curve rows; each run SHALL contain at most one record for each benchmark key.

#### Scenario: Persist dual benchmarks with one run
- **WHEN** a benchmark-enabled run is persisted
- **THEN** it has exactly one `equal_weight_monthly` child and exactly one `csi_300_buy_hold` child
- **AND** each child has its own ordered daily net-value rows

#### Scenario: Benchmark curve identity is unique
- **WHEN** persistence attempts to add two net-value rows for the same benchmark and trade date
- **THEN** the database rejects the duplicate

### Requirement: Query benchmark results with a run
The persisted-result query helper SHALL load ordered benchmark records and their ordered curve rows with a backtest run. Runs created before benchmark support SHALL remain queryable with an empty benchmark collection.

#### Scenario: Read legacy run
- **WHEN** a caller loads a pre-benchmark backtest run
- **THEN** the run is returned without modification
- **AND** its benchmark collection is empty
