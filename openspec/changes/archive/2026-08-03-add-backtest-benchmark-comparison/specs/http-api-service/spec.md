## ADDED Requirements

### Requirement: API backtest responses expose benchmark comparison
The successful backtest-run response and backtest-detail response SHALL expose an ordered collection containing both benchmark keys, names, five metrics, and strategy-minus-benchmark total-return and annualized-return differences. The detail response SHALL additionally expose ordered benchmark net-value curve points; legacy persisted runs SHALL return an empty collection rather than synthetic benchmark values.

#### Scenario: New backtest API response has two benchmarks
- **WHEN** a client runs or reads a newly completed benchmark-enabled backtest
- **THEN** the response contains `equal_weight_monthly` and `csi_300_buy_hold` exactly once
- **AND** each entry contains all five metrics and both relative-return differences

#### Scenario: Detail exposes benchmark curves
- **WHEN** a client requests the detail of a benchmark-enabled backtest
- **THEN** each benchmark entry includes net-value points ordered by trade date

#### Scenario: Legacy detail remains readable
- **WHEN** a client requests a persisted run with no benchmark records
- **THEN** the detail response succeeds with an empty benchmark collection
