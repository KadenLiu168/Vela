## ADDED Requirements

### Requirement: Backtest detail equity curve summary
The web frontend SHALL render a basic equity curve summary on the Backtest Detail page from valid `equity_curve` rows returned by `GET /api/backtests/{run_id}`.

#### Scenario: Backtest detail shows multi-point equity curve summary
- **WHEN** the Backtest Detail API returns two or more equity curve rows with finite net values
- **THEN** the Backtest Detail page shows the valid equity curve point count
- **AND** it shows the first valid trade date and net value
- **AND** it shows the last valid trade date and net value
- **AND** it shows the minimum and maximum valid net values

#### Scenario: Backtest detail shows single-point equity curve summary
- **WHEN** the Backtest Detail API returns exactly one valid equity curve point
- **THEN** the Backtest Detail page shows the valid equity curve point count
- **AND** it shows the point trade date and net value
- **AND** it does not draw a multi-point line chart

#### Scenario: Backtest detail summary uses real detail API data
- **WHEN** frontend validation renders the Backtest Detail route with a successful detail API response
- **THEN** the visible equity curve summary values come from the response `equity_curve` rows
- **AND** the page code uses the shared backtest detail API client helper instead of static curve summary data
