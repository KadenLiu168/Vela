## ADDED Requirements

### Requirement: Key frontend component regions have controlled fixture coverage
The web frontend SHALL validate critical local workflow component regions with controlled fixtures that match the real API response field names and nesting.

#### Scenario: Dashboard status blocks are covered
- **WHEN** frontend tests render the Dashboard route with a successful dashboard aggregate fixture
- **THEN** the tests MUST verify the Dashboard market data status block renders price rows, covered ETFs, trade-date boundaries, latest signal status, and recent backtest metric summary values from that fixture

#### Scenario: Target holdings table is covered
- **WHEN** frontend tests render the Signal Detail route with a successful latest-signal fixture containing positions
- **THEN** the tests MUST verify the target holdings table renders exchange, symbol, target weight, rank, score, and fallback fields from the fixture

#### Scenario: Backtest metric cards are covered
- **WHEN** frontend tests render the Backtest Detail route with a successful backtest detail fixture
- **THEN** the tests MUST verify the backtest metric cards render total return, annualized return, max drawdown, volatility, and Sharpe ratio fields from the fixture

#### Scenario: Error summaries are covered
- **WHEN** frontend tests trigger Dashboard operation failures or page-level API failures
- **THEN** the tests MUST verify concise user-visible error summaries render the failure type, reason, and next-step or API-unavailable message

### Requirement: Key frontend component states are covered
The web frontend SHALL validate loading, empty, and error states for key local workflow component regions.

#### Scenario: Loading states are covered
- **WHEN** frontend tests render Dashboard, Signal Detail, or Backtest Detail while the corresponding API request is pending
- **THEN** the tests MUST verify the relevant loading state is visible without rendering stale fixture data

#### Scenario: Empty states are covered
- **WHEN** frontend tests render successful API responses with missing local workflow data
- **THEN** the tests MUST verify empty states for missing Dashboard data, missing target holdings, and missing backtest detail chart data without treating the responses as failures

#### Scenario: Error states are covered
- **WHEN** frontend tests render rejected API requests or failed Dashboard operations
- **THEN** the tests MUST verify user-visible error states remain scoped to the affected page or operation region
