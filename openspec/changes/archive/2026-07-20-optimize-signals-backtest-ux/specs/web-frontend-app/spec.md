## MODIFIED Requirements

### Requirement: Signal history list page
The web frontend SHALL expose a `/signals` route rendering a paginated table of historical successful strategy signals for the current strategy and version, with each row linking to that signal's detail page. The page SHALL provide a SOURCE segmented filter (All / Manual / Scheduled / Backtest / Legacy) that drives server-side filtering via the API `source` parameter. The active non-All filter SHALL be reflected in the URL query as `?source=<value>`, while All SHALL omit the parameter. Changing the filter SHALL reset pagination to the first page.

#### Scenario: List renders signal rows
- **WHEN** the user navigates to `/signals` and successful signals exist
- **THEN** the page renders one row per signal showing at least signal id, signal date, config version, result, source, and generated timestamp
- **AND** each row links to `/signals/{signal_id}`

#### Scenario: List paginates history
- **WHEN** the signal history exceeds one page
- **THEN** the page provides pagination controls that request successive pages via limit and offset

#### Scenario: Source filter narrows the list
- **WHEN** the user selects the Backtest segment
- **THEN** the frontend requests the first page with `source=backtest`
- **AND** the table shows only entries returned for that source
- **AND** the URL query includes `source=backtest`

#### Scenario: All removes only the source query
- **WHEN** the user selects All while the URL contains `source=backtest` plus other query parameters or a hash
- **THEN** the next request omits `source`
- **AND** the URL removes only `source` while preserving the other query parameters and hash

#### Scenario: Valid source initializes the filter
- **WHEN** the user opens `/signals?source=scheduled`
- **THEN** Scheduled is active
- **AND** the first list request includes `source=scheduled`

#### Scenario: Invalid source URL is normalized
- **WHEN** the user opens `/signals` with an unknown, empty, or literal `null` source value
- **THEN** All is active and the list request omits `source`
- **AND** the invalid source parameter is removed from the URL without removing unrelated query parameters or the hash

#### Scenario: Empty signal history
- **WHEN** the user navigates to `/signals` and no successful signal exists
- **THEN** the page renders an empty state directing the user to generate a signal from the Dashboard

#### Scenario: Selected source has no results
- **WHEN** a valid non-All SOURCE filter returns no signals on its first page
- **THEN** the page renders an empty state naming or otherwise identifying the active filter

### Requirement: Backtest detail page fetches by id
The web frontend SHALL fetch the backtest detail for `/backtests/:id` by the route's run id, render a not-found state on 404, and organize the detail into two tabs: an Overview tab (run metadata, metrics, equity curve, parameters) shown by default, and a Signals (N) tab whose count comes from the detail response's `signal_count`. Users SHALL be able to inspect Overview content without first traversing the run's signal list. The Signals tab SHALL load paginated summary data only when activated and only when `signal_count > 0`.

#### Scenario: Detail fetches the requested id
- **WHEN** the user navigates to `/backtests/{run_id}`
- **THEN** the frontend calls the by-id backtest detail endpoint with that `run_id`
- **AND** the rendered detail corresponds to that run id

#### Scenario: Overview tab is visible by default
- **WHEN** the backtest detail loads
- **THEN** Overview is selected
- **AND** run metadata, metrics, equity curve, and parameters are in its tabpanel
- **AND** the Signals table is not rendered ahead of those sections

#### Scenario: Signals tab label reflects signal_count
- **WHEN** the backtest detail loads
- **THEN** the Signals tab label displays the detail response's `signal_count`

#### Scenario: Unknown or foreign run id shows not-found state
- **WHEN** the user navigates to `/backtests/{run_id}` and the detail API returns 404
- **THEN** the page renders a not-found empty state

#### Scenario: Route id change resets local detail state
- **WHEN** the mounted detail page changes from one `run_id` to another
- **THEN** Overview becomes active with Signals offset zero
- **AND** stale signal-page responses from the previous run do not render for the new run

### Requirement: Backtest detail lists its signals
The Backtest detail Signals tab SHALL render a compact table with columns Signal #, Signal date, Result, and an action link to each signal detail. It SHALL consume `GET /api/backtests/{run_id}/signals` using page size 20 and SHALL use detail `signal_count` to determine pagination boundaries. Because every linked signal has source `backtest`, the tab SHALL NOT present a source column, source filter, or source distribution. The tab SHALL show loading and error states using existing presentation primitives, and an explicit empty state when `signal_count` is zero.

#### Scenario: Signals tab shows a compact paginated table
- **WHEN** the user activates Signals for a run whose `signal_count` is greater than zero
- **THEN** the frontend requests offset zero from the paginated endpoint
- **AND** renders columns Signal #, Signal date, Result, and an action link
- **AND** renders pagination controls using `signal_count` as the known total

#### Scenario: Signals tab loads lazily
- **WHEN** the backtest detail loads with Overview active
- **THEN** the frontend does not request the backtest signals endpoint
- **AND** the first positive-count request occurs only after Signals is activated

#### Scenario: Zero-count tab avoids an unnecessary request
- **WHEN** the user activates Signals for a run whose `signal_count` is zero
- **THEN** the tab renders the no-linked-signals empty state
- **AND** does not request the paginated signals endpoint

#### Scenario: Pagination uses exact total boundaries
- **WHEN** the user views the final page and `signal_count` is an exact multiple of 20
- **THEN** Next is disabled
- **AND** the user cannot navigate to an empty page beyond the known total

#### Scenario: Signals tab has no source categorization
- **WHEN** the Signals tab renders
- **THEN** it contains no source column, source filter, or source distribution

#### Scenario: Signals tab loading and error states
- **WHEN** the paginated signals request is in flight or fails
- **THEN** the tab renders a loading or error `FeedbackMessage`
- **AND** a stale response for an earlier offset or run id does not replace the current state

### Requirement: Backtest detail tabs are keyboard accessible
The Backtest detail tabs SHALL implement an automatically activated two-tab interface using the ARIA tab pattern. Each tab SHALL identify and control one tabpanel; only the active tab SHALL be in the normal tab order.

#### Scenario: Tab semantics are connected
- **WHEN** the Backtest detail tabs render
- **THEN** their container has `role="tablist"`
- **AND** each tab has `role="tab"`, `aria-selected`, `aria-controls`, and a stable id
- **AND** each `role="tabpanel"` references its tab with `aria-labelledby`

#### Scenario: Keyboard changes the active tab
- **WHEN** focus is on a tab and the user presses ArrowLeft, ArrowRight, Home, or End
- **THEN** focus moves to the corresponding tab
- **AND** that tab becomes active

## ADDED Requirements

### Requirement: New signal and backtest UI follows existing presentation language
The SOURCE filter, Backtest tabs, and signals table SHALL reuse the existing panel, table, Pagination, DescriptionItem, EmptyState, and FeedbackMessage implementations where applicable, plus the design tokens in `tokens.css`. Because the repository has no existing general Tab or segmented-control primitive, those controls MAY use minimal page-scoped token-based styles. The implementation SHALL NOT duplicate existing primitive CSS or introduce a new general-purpose component abstraction for these single use cases.

#### Scenario: Source filter adds only necessary control styling
- **WHEN** the Signals list renders its SOURCE filter
- **THEN** the results panel and table reuse existing primitives
- **AND** any new segmented-control styles are page-scoped and use existing tokens

#### Scenario: Backtest tabs reuse existing content primitives
- **WHEN** the Backtest detail renders its tabs and signals table
- **THEN** tab content reuses the existing panel, table, Pagination, DescriptionItem, EmptyState, and FeedbackMessage implementations
- **AND** any new tab styles are minimal and token-based
