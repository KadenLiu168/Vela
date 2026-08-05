## ADDED Requirements

### Requirement: Persist nullable benchmark-regime fields
`BacktestBenchmark` SHALL expose nullable six-decimal `capm_alpha`, `capm_beta`, `capm_r_squared`, `up_capture_ratio`, and `down_capture_ratio` fields plus nullable integer `capm_observation_count`, `up_capture_observation_count`, and `down_capture_observation_count` fields. `capm_observation_count` SHALL count aligned daily sessions, while each capture observation count SHALL count selected calendar-month buckets. Persistence and query helpers SHALL round-trip the fields without recomputation and preserve stable benchmark ordering and ownership.

#### Scenario: Newly calculated benchmark children round-trip metrics
- **WHEN** a benchmark-enabled result with calculated regime metrics is persisted and queried in a fresh session
- **THEN** every value and observation count returns on its owning benchmark child
- **AND** equal-weight CAPM fields remain null

### Requirement: Benchmark-regime migration preserves legacy history
The Alembic migration SHALL add only nullable benchmark-regime columns and MUST NOT backfill or recalculate historical results. Legacy runs and benchmark rows SHALL remain readable with null new fields, and downgrade SHALL remove only the columns introduced by this Change.

#### Scenario: Legacy database upgrades and downgrades without fabrication
- **WHEN** a file-backed SQLite database containing legacy strategy, benchmark, and curve rows is upgraded and downgraded through the new revision
- **THEN** all pre-existing rows and metric values remain unchanged
- **AND** upgraded legacy benchmark rows expose null benchmark-regime fields
