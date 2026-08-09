## MODIFIED Requirements

### Requirement: Signal history list page
The web frontend SHALL expose a `/signals` route rendering a paginated table of historical successful strategy signals for the current strategy and version, with each row linking to that signal's detail page. The page SHALL provide a SOURCE filter button group (All / Manual / Scheduled / Backtest / Legacy) that drives server-side filtering via the API `source` parameter. The filter buttons SHALL use the `button-secondary` variant; the active non-All option SHALL render with the variant's pressed state (inverted fill via `aria-pressed="true"`). The active non-All filter SHALL be reflected in the URL query as `?source=<value>`, while All SHALL omit the parameter. Changing the filter SHALL reset pagination to the first page.

#### Scenario: List renders signal rows
- **WHEN** the user navigates to `/signals` and successful signals exist
- **THEN** the page renders one row per signal showing at least signal id, signal date, config version, result, source, and generated timestamp
- **AND** each row links to `/signals/{signal_id}`

#### Scenario: List paginates history
- **WHEN** the signal history exceeds one page
- **THEN** the page provides pagination controls that request successive pages via limit and offset

#### Scenario: Source filter narrows the list
- **WHEN** the user selects the Backtest filter button
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

#### Scenario: Filter buttons use the secondary variant with a pressed state
- **WHEN** the user navigates to `/signals`
- **THEN** every SOURCE filter button MUST carry the `button-secondary` variant className
- **AND** the active option MUST carry `aria-pressed="true"` and render with the inverted fill
