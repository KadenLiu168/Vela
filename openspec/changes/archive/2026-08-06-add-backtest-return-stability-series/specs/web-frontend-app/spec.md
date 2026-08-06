## ADDED Requirements

### Requirement: Backtest Detail provides selectable rolling diagnostics
Backtest Detail SHALL present a Stability section with an explicit 63-session window label and a selector for Rolling Return, Rolling Volatility, and Rolling Sharpe. The selected view SHALL compare strategy and available fixed benchmarks using API-provided values, identify window dates and entity names accessibly, and provide a semantic tabular/text alternative. It MUST NOT calculate values in the browser or mix differently scaled metrics on one axis.

#### Scenario: User switches rolling metric without recomputation
- **WHEN** a user selects Return, Volatility, or Sharpe
- **THEN** the chart and accessible value representation use the corresponding API series unchanged
- **AND** retain distinguishable strategy and benchmark identities

#### Scenario: Short or legacy run explains unavailability
- **WHEN** rolling status is insufficient or Sharpe status lacks risk-free-rate evidence
- **THEN** the UI explains the specific unavailable scope
- **AND** continues to show every available stability metric and existing Backtest Detail content

### Requirement: Backtest Detail presents monthly and yearly returns
The Stability section SHALL provide monthly and yearly views with an entity selector for strategy and available fixed benchmarks. Every visible and accessible period value SHALL expose its period, compounded return, observation count, and requested-scope partial marker using the exact API result. The UI MUST NOT describe that marker as proof of complete official-session evidence.

#### Scenario: Requested-scope partial periods remain visible and distinguishable
- **WHEN** calendar return data includes partial boundary buckets
- **THEN** those buckets remain visible with a clear requested-period partial label
- **AND** are not silently dropped or presented as complete periods

### Requirement: Stability presentation is responsive and accessible
Rolling controls, charts, tables/heatmaps, entity selection, empty/error states, and existing Backtest Detail tabs/actions SHALL be keyboard accessible and programmatically labeled. The page SHALL avoid page-level horizontal overflow and retain readable hierarchy at 1440x1000 and 390x844.

#### Scenario: Required viewports preserve analysis and navigation
- **WHEN** stability content renders at either required viewport
- **THEN** users can reach selectors, inspect exact values and partial states, and use existing Backtest Detail actions
- **AND** the page has no page-level horizontal overflow

### Requirement: Walk-forward parent does not present stitched stability
Walk-forward Detail SHALL NOT show rolling or calendar-period metrics derived from `stitched_oos`. Existing links to selected OOS Backtest Detail pages SHALL remain the path for inspecting each independent window's stability series.

#### Scenario: Available stitched curve retains reset-only semantics
- **WHEN** Walk-forward Detail renders an available stitched OOS curve
- **THEN** it shows no stitched Rolling Sharpe, Volatility, Return, monthly return, or yearly return
- **AND** linked OOS Backtest Detail pages remain navigable
