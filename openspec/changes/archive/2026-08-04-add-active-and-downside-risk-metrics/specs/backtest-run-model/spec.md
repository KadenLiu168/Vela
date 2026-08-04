## ADDED Requirements

### Requirement: Persist expanded strategy and benchmark metric fields
`BacktestRun` SHALL expose nullable `sortino_ratio`, `calmar_ratio`, `longest_drawdown_duration_sessions`, `longest_drawdown_peak_date`, `longest_drawdown_trough_date`, and `longest_drawdown_recovery_date` fields. `BacktestBenchmark` SHALL expose the same nullable absolute fields plus nullable `tracking_error` and `information_ratio` fields. Decimal metrics SHALL use the existing six-decimal metric storage convention.

#### Scenario: New run persists expanded fields
- **WHEN** a newly completed benchmark-enabled run has calculable expanded metrics
- **THEN** its strategy row and both benchmark child rows retain their typed values
- **AND** each benchmark retains TE/IR relative to that strategy run

#### Scenario: Flat new run distinguishes zero duration
- **WHEN** a newly completed run has no underwater interval
- **THEN** duration sessions is zero and its duration dates are null

### Requirement: Expanded metric migration preserves legacy history
The Alembic migration SHALL add only nullable expanded-metric columns and MUST NOT backfill or recalculate historical results. Legacy strategy and benchmark rows SHALL remain readable with null expanded fields. Downgrade SHALL remove only the new columns.

#### Scenario: Legacy run upgrades without fabricated metrics
- **WHEN** a database containing a legacy run and benchmark rows is upgraded
- **THEN** the existing rows and five original metric values are unchanged
- **AND** all expanded fields are null

#### Scenario: Migration round trip preserves original data
- **WHEN** the expanded-metric revision is upgraded and downgraded on file-backed SQLite
- **THEN** pre-existing run, benchmark and curve data remain intact
