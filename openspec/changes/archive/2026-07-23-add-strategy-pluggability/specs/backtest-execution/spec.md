## ADDED Requirements

### Requirement: Strategy-declared price panel lookback
The backtest SHALL resolve the selected bound strategy and size the price-panel start from its non-negative `lookback_days()` value rather than reading strategy-specific config fields. Lookback SHALL mean the number of prior trading sessions, excluding the signal session; the calendar buffer SHALL therefore provide enough observations for calculations that require the signal row plus that history.

#### Scenario: Dual-momentum lookback sizes the price panel
- **WHEN** a backtest uses dual momentum
- **THEN** lookback is the maximum short, long, and moving-average window
- **AND** the panel start uses the existing safe calendar conversion from that value
- **AND** backtest_runner does not read dual-momentum parameter fields

#### Scenario: Long-window return has signal plus prior observations
- **WHEN** dual momentum declares a long lookback of N prior sessions
- **THEN** the loaded/truncated series can include N prior observations plus the signal-date observation when local data is complete

#### Scenario: Zero-lookback strategy uses minimal buffer
- **WHEN** a strategy declares lookback 0
- **THEN** the panel start uses only the existing minimal calendar buffer
- **AND** the backtest does not require historical momentum/trend data

#### Scenario: Invalid negative lookback is rejected
- **WHEN** a registered strategy returns a negative lookback
- **THEN** backtest execution fails clearly before loading a price panel or persisting a run

### Requirement: Backtest orchestration is strategy-agnostic
Backtest execution SHALL resolve strategies through the registry, invoke generic historical signal generation, and retain the existing persistence, linkage, holdings, equity, metric, data-quality, and caller-managed transaction behavior. The persisted `parameters_json` audit payload SHALL include the selected strategy `type` in addition to the existing identity/date/risk-free-rate fields.

#### Scenario: Historical loop invokes protocol per rebalance date
- **WHEN** a backtest runs either registered strategy
- **THEN** each rebalance date is generated through the bound protocol
- **AND** no concrete strategy is imported or branched on in backtest_runner

#### Scenario: Strategy switch preserves downstream flow
- **WHEN** the same date range is run with distinct dual-momentum and equal-weight config identities
- **THEN** both runs use the same downstream persistence, linkage, holdings, equity, and metric code
- **AND** each run selects only signals from its own strategy_id and config_version

#### Scenario: Backtest audit payload records strategy type
- **WHEN** a backtest run is persisted
- **THEN** its `parameters_json` includes the selected config `type`
- **AND** no database schema change is required
