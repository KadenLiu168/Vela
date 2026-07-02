## ADDED Requirements

### Requirement: Frontend page loading feedback
The web frontend SHALL render a consistent page-loading feedback state while Dashboard, Signal Detail, or Backtest Detail data requests are pending.

#### Scenario: Dashboard shows page loading feedback
- **WHEN** the Dashboard route is waiting for `GET /api/dashboard`
- **THEN** the page shows a clear loading feedback state without placeholder successful data

#### Scenario: Signal detail shows page loading feedback
- **WHEN** the Signal Detail route is waiting for `GET /api/strategy-signals/latest`
- **THEN** the page shows a clear loading feedback state without placeholder signal data

#### Scenario: Backtest detail shows page loading feedback
- **WHEN** the Backtest Detail route is waiting for `GET /api/backtests/{run_id}`
- **THEN** the page shows a clear loading feedback state without placeholder run data

### Requirement: Dashboard operation feedback and concurrency protection
The web frontend SHALL render explicit Dashboard operation feedback for market data fetch, signal generation, and backtest run operations, and MUST prevent duplicate or conflicting Dashboard operations while any one of those operations is pending.

#### Scenario: Market data fetch shows pending and completion feedback
- **WHEN** a user starts an incremental or full market data fetch
- **THEN** the Dashboard shows an in-progress feedback state for the active fetch
- **AND** duplicate market data fetch submissions are prevented while the fetch is pending
- **AND** signal generation and backtest run submissions are disabled while the fetch is pending
- **AND** the Operations panel shows success or failure feedback after the fetch completes

#### Scenario: Signal generation shows pending and completion feedback
- **WHEN** a user starts signal generation
- **THEN** the Dashboard shows an in-progress feedback state for signal generation
- **AND** duplicate signal-generation submissions are prevented while generation is pending
- **AND** market data fetch and backtest run submissions are disabled while generation is pending
- **AND** the Operations panel shows success or failure feedback after generation completes

#### Scenario: Backtest run shows pending and completion feedback
- **WHEN** a user submits a valid backtest date range
- **THEN** the Dashboard shows an in-progress feedback state for the backtest run
- **AND** duplicate backtest submissions are prevented while the run is pending
- **AND** market data fetch and signal generation submissions are disabled while the run is pending
- **AND** the Operations panel shows success or failure feedback after the run completes
