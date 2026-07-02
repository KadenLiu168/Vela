## ADDED Requirements

### Requirement: Dashboard operation error summaries
The web frontend SHALL render user-understandable operation-level error summaries when Dashboard market data fetch, signal generation, or backtest run requests fail.

#### Scenario: Market data fetch request failure shows reason and next step
- **WHEN** the Dashboard market data fetch request fails with an API error response
- **THEN** the Operations panel shows that the market data fetch failed
- **AND** it shows a readable reason from the API error response when one is available
- **AND** it shows guidance to retry after checking data source availability and local ETF/data state
- **AND** the API error response text is not the only visible failure guidance

#### Scenario: Signal generation request failure shows reason and next step
- **WHEN** the Dashboard signal generation request fails with an API error response
- **THEN** the Operations panel shows that signal generation failed
- **AND** it shows a readable reason from the API error response when one is available
- **AND** it shows guidance to fetch market data or review local strategy configuration before retrying
- **AND** the API error response text is not the only visible failure guidance

#### Scenario: Backtest run request failure shows reason and next step
- **WHEN** the Dashboard run-backtest request fails with an API error response
- **THEN** the Operations panel shows that the backtest run failed
- **AND** it shows a readable reason from the API error response when one is available
- **AND** it shows guidance to verify the date range and available local market data or signals before retrying
- **AND** the API error response text is not the only visible failure guidance

#### Scenario: Operation error summaries avoid raw technical text as sole guidance
- **WHEN** an operation request fails with a technical API error detail such as a database exception or stack-like text
- **THEN** the Operations panel still shows operation-specific next-step guidance
- **AND** it does not rely on the raw technical detail as the only visible user prompt
