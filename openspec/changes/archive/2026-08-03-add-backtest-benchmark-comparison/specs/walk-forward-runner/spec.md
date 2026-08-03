## ADDED Requirements

### Requirement: OOS dual-benchmark comparison
For every selected OOS window, the walk-forward report SHALL retain and print metrics and relative total-return/CAGR differences for both fixed benchmarks. Its aggregate comparison section SHALL report the mean and contributing-window count for each benchmark's non-null total-return and annualized-return difference.

#### Scenario: Multiple OOS windows retain both comparisons
- **WHEN** a walk-forward run completes multiple OOS windows
- **THEN** each window identifies both fixed benchmarks and their comparison values
- **AND** aggregate comparison values exclude only null values for their own metric

## REMOVED Requirements

### Requirement: Baseline comparison
**Reason**: The configurable equal-weight baseline can inherit a non-monthly base cadence and cannot express the mandatory CSI 300 buy-and-hold comparison.

**Migration**: Remove `baseline` from walk-forward YAML/configuration and consume the fixed `equal_weight_monthly` and `csi_300_buy_hold` results from each OOS window instead.
