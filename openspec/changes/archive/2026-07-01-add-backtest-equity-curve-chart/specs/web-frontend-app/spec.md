## ADDED Requirements

### Requirement: Backtest detail equity curve chart
The web frontend SHALL render a net value equity curve on the Backtest Detail page from the `GET /api/backtests/{run_id}` response.

#### Scenario: Backtest detail shows net value line chart
- **WHEN** the Backtest Detail API returns two or more equity curve rows with trade dates and finite net values
- **THEN** the Backtest Detail page renders a line chart using those `trade_date` and `net_value` values
- **AND** the chart is labeled as the equity curve

#### Scenario: Backtest detail handles empty equity curve
- **WHEN** the Backtest Detail API returns no valid equity curve points
- **THEN** the Backtest Detail page shows a clear empty equity curve state
- **AND** the page does not treat the successful API response as an error

#### Scenario: Backtest detail handles single equity curve point
- **WHEN** the Backtest Detail API returns exactly one valid equity curve point
- **THEN** the Backtest Detail page shows the single trade date and net value as a limited curve state
- **AND** the page does not draw a multi-point line chart

#### Scenario: Backtest detail limits first chart scope
- **WHEN** the Backtest Detail page renders equity curve data
- **THEN** it does not render a drawdown curve, monthly returns chart, or return distribution chart
