# web-client-routing Specification Delta

## MODIFIED Requirements

### Requirement: Declarative browser route map owns the web application
The web application SHALL use a `BrowserRouter`-backed declarative route tree as the sole owner of browser-history route selection. The tree SHALL render the existing public paths without changing their meanings: `/` for Dashboard, `/signals` and `/signals/:signalId` for Signal history/detail, `/backtests` and `/backtests/:backtestId` for Backtest history/detail, `/walk-forwards` and `/walk-forwards/:runId` for Walk-forward history/detail, and `/etfs/:etfId` for ETF detail.

#### Scenario: Direct valid path renders its established page
- **WHEN** a user opens any declared list path or a declared detail path with a decimal identifier
- **THEN** the Router renders the page associated with that exact path
- **AND** the page retains its existing API request, loading, success, empty, and valid-id API-not-found behavior
- **AND** a failed read keeps the Router-rendered page mounted and may present an actionable cause and an in-page retry as specified by `web-read-failure-recovery`

#### Scenario: Browser history changes render through the route tree
- **WHEN** a user uses the browser Back or Forward control between declared application paths
- **THEN** the visible page changes to the history entry selected by the browser
- **AND** the application does not depend on an application-owned `popstate` listener or a synthetic `PopStateEvent`
