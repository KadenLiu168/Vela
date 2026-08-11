## ADDED Requirements

### Requirement: Declarative browser route map owns the web application
The web application SHALL use a `BrowserRouter`-backed declarative route tree as the sole owner of browser-history route selection. The tree SHALL render the existing public paths without changing their meanings: `/` for Dashboard, `/signals` and `/signals/:signalId` for Signal history/detail, `/backtests` and `/backtests/:backtestId` for Backtest history/detail, `/walk-forwards` and `/walk-forwards/:runId` for Walk-forward history/detail, and `/etfs/:etfId` for ETF detail.

#### Scenario: Direct valid path renders its established page
- **WHEN** a user opens any declared list path or a declared detail path with a decimal identifier
- **THEN** the Router renders the page associated with that exact path
- **AND** the page retains its existing API request, loading, success, empty, error, and valid-id API-not-found behavior

#### Scenario: Browser history changes render through the route tree
- **WHEN** a user uses the browser Back or Forward control between declared application paths
- **THEN** the visible page changes to the history entry selected by the browser
- **AND** the application does not depend on an application-owned `popstate` listener or a synthetic `PopStateEvent`

### Requirement: Internal navigation remains within the mounted application
Every production navigation to a Vela application path SHALL use Router link or Router navigation primitives. This includes AppShell navigation, Dashboard summary and ETF detail entries, Signal list/detail entries, Backtest list/detail entries, Walk-forward list/detail entries, command-palette page/backtest selections, and the redirect after an accepted Walk-forward run. These transitions SHALL NOT reload the document.

#### Scenario: Detail link preserves lifted Dashboard form state
- **WHEN** a user enters backtest start and end dates on Dashboard, follows an internal detail link, and returns to Dashboard during the same application session
- **THEN** the Dashboard backtest form shows the previously entered dates
- **AND** the navigation completes without a document reload

#### Scenario: Primary navigation exposes Router-managed active state
- **WHEN** a user opens `/signals` or `/signals/{signalId}` through the application
- **THEN** the Signals primary navigation entry is exposed as the current page
- **AND** the existing navigation link styling and accessible `aria-current` behavior remain available

#### Scenario: Programmatic navigation uses the Router
- **WHEN** a user selects a navigable command-palette row or a Walk-forward run reaches successful completion
- **THEN** the URL and rendered page change to the selected route through Router navigation
- **AND** no page component mutates `window.history` or dispatches a synthetic browser-history event for that transition

### Requirement: Signal source-query ownership uses Router location state
The Signal history source filter SHALL derive its value from Router-managed location search state and SHALL update that search state through Router navigation. A valid source selection SHALL retain the existing filter, pagination-reset, unrelated-query-parameter, and hash behavior.

#### Scenario: Source selection preserves unrelated URL state
- **WHEN** a user changes the Signal history source while the current URL has unrelated query parameters and a hash
- **THEN** the URL contains the selected valid `source` value or omits `source` for All
- **AND** unrelated query parameters and the hash remain unchanged
- **AND** the list reloads from offset zero for the selected source

#### Scenario: Invalid source value is normalized through Router navigation
- **WHEN** a user opens `/signals` with an invalid `source` query value
- **THEN** the filter behaves as All
- **AND** Router replacement navigation removes only the invalid `source` value while preserving unrelated query parameters and the hash

### Requirement: Invalid and unmatched paths render a not-found page
The Router SHALL accept detail identifiers only when the dynamic segment contains one or more decimal digits, matching the former route contract. An invalid or missing detail identifier, or any path outside the declared route tree, SHALL render an explicit not-found page inside AppShell rather than Dashboard and SHALL not issue a detail API request. The not-found page SHALL expose one page-level heading and a Router link to Dashboard.

#### Scenario: Malformed detail identifier is rejected before API access
- **WHEN** a user opens `/signals/abc`, `/backtests/abc`, `/walk-forwards/abc`, or `/etfs/abc`
- **THEN** the application renders the explicit not-found page
- **AND** it does not request the corresponding detail API endpoint

#### Scenario: Unknown path is not rendered as Dashboard
- **WHEN** a user opens an unmatched path such as `/foo`
- **THEN** the application renders the explicit not-found page inside the persistent AppShell
- **AND** it does not render Dashboard as a fallback
