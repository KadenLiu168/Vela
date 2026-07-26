## MODIFIED Requirements

### Requirement: Persist normalized backtest results
The system SHALL persist backtest results using the actual normalized portfolio state produced by equity-curve calculation and SHALL identify the shared equity calculation semantics in run parameters.

#### Scenario: Persist successful run
- **WHEN** backend code completes a backtest
- **THEN** the system persists a new `BacktestRun` row with parameters, status, metrics, and timestamps
- **AND** persists `BacktestEquityCurve` rows for each equity curve point

#### Scenario: Normalized curve rows
- **WHEN** backend code maps an equity curve point with holdings to a persisted curve row
- **THEN** `total_assets` equals net value
- **AND** `market_value` equals net value
- **AND** `cash` equals `0.000000`
- **AND** `positions_json` includes the target holdings for that date

#### Scenario: Empty holdings curve row
- **WHEN** backend code maps an equity curve point without holdings to a persisted curve row
- **THEN** `total_assets` equals net value
- **AND** `market_value` equals `0.000000`
- **AND** `cash` equals net value
- **AND** `positions_json` stores an empty list

#### Scenario: Persist successful drift-model run
- **WHEN** backend code completes a backtest using the continuous portfolio-state equity model
- **THEN** the system persists a new `BacktestRun` row with parameters, status, metrics, and timestamps
- **AND** `parameters_json` contains `equity_model_version` equal to `"drift_v1"`
- **AND** the system persists one `BacktestEquityCurve` row for each equity curve point

#### Scenario: Persist invested curve row
- **WHEN** backend code maps a curve point with risky-asset holdings to a persisted row
- **THEN** `total_assets` equals net value
- **AND** `cash` and `market_value` equal the curve point's calculated normalized state
- **AND** `cash + market_value` equals `total_assets`
- **AND** `positions_json` includes each ETF's `etf_id`, signal `target_weight`, and calculated `actual_weight`

#### Scenario: Persist drifted holdings
- **WHEN** a curve point's actual weights differ from its carried signal target weights
- **THEN** `positions_json` preserves both values without replacing the actual weights with target weights

#### Scenario: Persist cash-only curve row
- **WHEN** backend code maps a curve point without risky-asset holdings
- **THEN** `total_assets` equals net value
- **AND** `market_value` equals `0.000000`
- **AND** `cash` equals net value
- **AND** `positions_json` stores an empty list

#### Scenario: Runner consumes calculated state once
- **WHEN** the runner maps equity points for persistence
- **THEN** it consumes the state carried by those equity points
- **AND** it does not independently reconstruct cash, market value, or actual positions from target holding snapshots

#### Scenario: Runner rejects a point without calculated state
- **WHEN** the runner is asked to map an equity point that does not carry calculator-produced portfolio state
- **THEN** it fails explicitly instead of persisting fabricated cash, market value, or positions

#### Scenario: Historical runs remain unchanged
- **WHEN** the drift model is deployed
- **THEN** existing backtest rows are not mutated, deleted, labeled, or automatically regenerated
- **AND** runs without `equity_model_version: "drift_v1"` are not assumed to be directly comparable with drift-model runs
