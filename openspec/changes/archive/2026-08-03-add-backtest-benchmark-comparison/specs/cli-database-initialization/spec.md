## ADDED Requirements

### Requirement: CLI backtest benchmark comparison
The `run-backtest` command and exported backtest report SHALL identify both fixed benchmarks, show their five metrics, and show strategy-minus-benchmark total-return and annualized-return differences for benchmark-enabled runs.

#### Scenario: CLI prints benchmark summary
- **WHEN** a user runs a successful benchmark-enabled backtest through the CLI
- **THEN** stdout identifies both benchmarks and their comparison values in addition to the strategy summary

#### Scenario: Exported report prints benchmark summary
- **WHEN** a user exports a benchmark-enabled backtest report
- **THEN** the report contains separate sections for both benchmarks and their two relative return differences
