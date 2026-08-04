## ADDED Requirements

### Requirement: Selected OOS evidence includes expanded risk metrics
After `strengthen-walk-forward-evaluation-contract`, each selected OOS window SHALL retain strategy Sortino, Calmar and longest drawdown duration and each fixed benchmark comparison SHALL retain Tracking Error and Information Ratio. The report SHALL aggregate each strategy metric and each benchmark-relative metric separately using the existing metric-local valid-count and evidence-status contract.

#### Scenario: OOS windows aggregate downside metrics
- **WHEN** three selected OOS runs contain valid Sortino and Calmar values
- **THEN** the evidence report includes their descriptive summaries and sufficient valid counts

#### Scenario: Benchmark active metrics remain keyed
- **WHEN** selected OOS runs contain TE/IR for both fixed benchmarks
- **THEN** the report aggregates TE/IR separately for `equal_weight_monthly` and `csi_300_buy_hold`

#### Scenario: Expanded evidence does not join curves
- **WHEN** expanded OOS metrics are reported across adjacent windows
- **THEN** the windows remain independent
- **AND** no continuous OOS curve or cross-window Calmar/drawdown duration is calculated
