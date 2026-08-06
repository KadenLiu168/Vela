## ADDED Requirements

### Requirement: Distribution metrics participate in atomic execution
Normal success/partial and selected Walk-forward OOS execution SHALL calculate strategy and fixed-benchmark tail-distribution metrics before persistence. Isolated benchmark-skipping training trials SHALL calculate the strategy-only family for selection evidence without writing it to the source database. All source-side calculation and persistence SHALL remain inside the existing caller-owned transaction.

#### Scenario: Completed benchmark-enabled run persists one versioned family
- **WHEN** strategy and benchmark distribution calculations complete successfully
- **THEN** their metrics and counts persist atomically on the owning records
- **AND** the run snapshot records `tail_distribution_metrics_v1`

#### Scenario: Insufficient sample persists evidence counts and null metrics
- **WHEN** a completed curve has fewer than 100 effective returns
- **THEN** its owner persists actual observation/tail counts and null distribution metrics

#### Scenario: Late failure rolls back every artifact
- **WHEN** distribution calculation, validation, or persistence fails after source-side artifacts have been added
- **THEN** the caller-managed transaction commits no signal, run, curve, benchmark, existing metric, or distribution metric from the attempt

#### Scenario: Training trial remains isolated
- **WHEN** Walk-forward evaluates a benchmark-skipping training combination
- **THEN** its strategy-only distribution calculation and version remain inside the isolated snapshot
- **AND** no training metric or count is persisted to the source database
