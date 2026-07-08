## ADDED Requirements

### Requirement: Signal history list page
The web frontend SHALL expose a `/signals` route rendering a paginated table of historical successful strategy signals for the current strategy and version, with each row linking to that signal's detail page.

#### Scenario: List renders signal rows
- **WHEN** the user navigates to `/signals` and successful signals exist
- **THEN** the page renders one row per signal showing at least signal id, signal date, config version, result, and generated timestamp
- **AND** each row links to `/signals/{signal_id}`

#### Scenario: List paginates history
- **WHEN** the signal history exceeds one page
- **THEN** the page provides pagination controls that request successive pages via limit and offset

#### Scenario: Empty signal history
- **WHEN** the user navigates to `/signals` and no successful signal exists
- **THEN** the page renders an empty state directing the user to generate a signal from the Dashboard

### Requirement: Backtest history list page
The web frontend SHALL expose a `/backtests` route rendering a paginated table of historical backtest runs for the current strategy and version, with each row linking to that run's detail page.

#### Scenario: List renders backtest rows
- **WHEN** the user navigates to `/backtests` and backtest runs exist
- **THEN** the page renders one row per run showing at least run id, date range, status, and started timestamp
- **AND** each row links to `/backtests/{run_id}`

#### Scenario: List paginates history
- **WHEN** the backtest history exceeds one page
- **THEN** the page provides pagination controls that request successive pages via limit and offset

#### Scenario: Empty backtest history
- **WHEN** the user navigates to `/backtests` and no backtest run exists
- **THEN** the page renders an empty state directing the user to run a backtest from the Dashboard

### Requirement: Signal detail page fetches by id
The web frontend SHALL fetch the signal detail for `/signals/:id` by the route's signal id, not by a latest-only API.

#### Scenario: Detail fetches the requested id
- **WHEN** the user navigates to `/signals/{signal_id}`
- **THEN** the frontend calls the by-id signal detail endpoint with that `signal_id`
- **AND** the rendered detail corresponds to that signal id

#### Scenario: Unknown or foreign signal id shows not-found state
- **WHEN** the user navigates to `/signals/{signal_id}` and the API returns 404
- **THEN** the page renders a not-found empty state

### Requirement: Backtest detail page fetches by id
The web frontend SHALL fetch the backtest detail for `/backtests/:id` by the route's run id, and render a not-found state on 404.

#### Scenario: Detail fetches the requested id
- **WHEN** the user navigates to `/backtests/{run_id}`
- **THEN** the frontend calls the by-id backtest detail endpoint with that `run_id`
- **AND** the rendered detail corresponds to that run id

#### Scenario: Unknown or foreign run id shows not-found state
- **WHEN** the user navigates to `/backtests/{run_id}` and the API returns 404
- **THEN** the page renders a not-found empty state

### Requirement: Signal and backtest browse navigation entries
The web frontend SHALL expose nav entries "Signals" pointing to `/signals` and "Backtests" pointing to `/backtests` as the canonical browse entry points.

#### Scenario: Nav offers signal and backtest list entries
- **WHEN** the user inspects the primary navigation
- **THEN** the nav includes a "Signals" entry with href `/signals`
- **AND** the nav includes a "Backtests" entry with href `/backtests`
- **AND** no nav entry points to `/signals/demo-signal`
