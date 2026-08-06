## ADDED Requirements

### Requirement: Persist nullable strategy and benchmark distribution fields
`BacktestRun` and `BacktestBenchmark` SHALL expose nullable six-decimal `historical_var_95`, `historical_cvar_95`, `return_skewness`, and `return_excess_kurtosis` fields plus nullable integer `distribution_observation_count` and `tail_observation_count` fields. New calculated rows SHALL store non-negative counts even when metrics are null; persistence/query helpers SHALL round-trip them without recomputation.

#### Scenario: Sufficient and insufficient owners round-trip exactly
- **WHEN** one newly persisted owner has sufficient evidence and another has insufficient evidence
- **THEN** a fresh-session query returns exact metrics/counts for the first and null metrics with actual counts for the second

### Requirement: Distribution migration preserves legacy history
The Alembic migration SHALL add only nullable distribution fields to strategy and benchmark tables and MUST NOT backfill or recalculate historical rows. Legacy rows SHALL remain readable with every new field null; downgrade SHALL remove only fields introduced by this Change.

#### Scenario: Legacy file-backed database survives upgrade and downgrade
- **WHEN** a test-owned file-backed SQLite database with existing runs, benchmarks, and curves is upgraded and downgraded through the new revision
- **THEN** all pre-existing rows and metric values remain unchanged
- **AND** upgraded legacy owners expose null distribution fields
