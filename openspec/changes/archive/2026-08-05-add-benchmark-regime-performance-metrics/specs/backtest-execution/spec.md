## ADDED Requirements

### Requirement: Benchmark-regime metrics participate in atomic execution
After strategy and fixed benchmark curves pass existing completeness checks, normal success/partial and selected Walk-forward OOS execution SHALL calculate benchmark-regime metrics before persistence. The calculation and all new fields SHALL remain inside the existing caller-owned transaction; a later calculation, validation, or persistence failure MUST roll back signals, runs, curves, benchmarks, existing metrics, and new comparison metrics together.

#### Scenario: Successful benchmark-enabled execution persists one versioned set
- **WHEN** a normal or selected OOS backtest completes benchmark-regime calculation successfully
- **THEN** it persists both benchmark comparison results atomically
- **AND** its parameter snapshot records `benchmark_regime_metrics_v1`

#### Scenario: Late regime-metric failure leaves no partial run
- **WHEN** benchmark-regime calculation or persistence fails after source-side artifacts have been added
- **THEN** the caller-managed transaction commits none of those artifacts

#### Scenario: Training execution keeps its existing scope
- **WHEN** an isolated Walk-forward training trial skips benchmark calculation
- **THEN** it does not calculate or persist CAPM or capture metrics
