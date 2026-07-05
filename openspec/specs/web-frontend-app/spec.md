# web-frontend-app Specification

## Purpose
TBD - created by archiving change 2026-07-05-add-setup-bootstrap-endpoint. Update Purpose after archive.
## Requirements
### Requirement: Dashboard setup bootstrap action
The web frontend SHALL expose a Dashboard action that triggers the local setup bootstrap endpoint through the shared frontend API client and renders a three-step status display.

#### Scenario: User triggers bootstrap from the Dashboard
- **WHEN** the Dashboard route has loaded or is able to render its operation section
- **AND** the user clicks the "Bootstrap / Setup database & data" action
- **THEN** the frontend sends `POST /api/setup/bootstrap` through the shared API client
- **AND** the action shows an in-progress state while the request is pending
- **AND** the action prevents duplicate submissions while the request is pending

#### Scenario: Dashboard shows three-step status during and after bootstrap
- **WHEN** the bootstrap request returns a response
- **THEN** the Dashboard renders one status row per bootstrap step (`migrate`, `sync_etf_pool`, `fetch_full_market_data`) using the response's `steps` array
- **AND** each status row shows a success or failure indicator matching the step's `status`
- **AND** a failed step row shows the step's `error_message`
- **AND** the Dashboard shows the response's `total_duration_seconds` as a final total once all steps have settled

#### Scenario: Dashboard refreshes aggregate data after successful bootstrap
- **WHEN** the bootstrap request returns a response with `status = "success"`
- **THEN** the Dashboard reloads aggregate data from `GET /api/dashboard`
- **AND** the refreshed market data status, latest signal status, and recent backtest status are rendered from the latest Dashboard response

### Requirement: Bootstrap button uses primary visual variant
The web frontend SHALL render the "Bootstrap / Setup database & data" Dashboard action in the primary (filled) button variant and SHALL place it at the right end of the Dashboard action list.

#### Scenario: Bootstrap button visual treatment
- **WHEN** the Dashboard renders its action list
- **THEN** the bootstrap action uses the primary (filled) button variant
- **AND** the bootstrap action is the rightmost button in the action list
- **AND** the existing "Fetch market data", "Full fetch", and "Generate signal" buttons continue to use the secondary (outline) variant

### Requirement: Compact-list label-value alignment and spacing
The web frontend SHALL render `compact-list` definition lists with baseline-aligned label-value pairs per grid row and sufficient vertical spacing between rows across all pages (Dashboard, Signal Detail, Backtest Detail).

#### Scenario: Label and value text baselines align within each row
- **WHEN** any page renders a `<dl className="compact-list">` with `<dt>` labels and `<dd>` values at desktop or tablet viewport widths
- **THEN** the label text and value text in the same grid row share the same text baseline
- **AND** the visual alignment is achieved via `align-items: baseline` on the grid container

#### Scenario: Row spacing is generous enough for mixed-font-size rows
- **WHEN** any page renders a `compact-list` at desktop or tablet viewport widths
- **THEN** the vertical gap between consecutive rows is at least 16px (`--spacing-16`)
- **AND** the larger value text (13px) in one row does not appear to crowd the label text (11px) in the next row

#### Scenario: Column spacing is preserved across page scopes
- **WHEN** any page renders a `compact-list`
- **THEN** the horizontal column gap between labels and values retains its existing per-scope value (16px for Dashboard/Backtest Detail, 20px for Signal Detail)

#### Scenario: Single-column mobile layout is unaffected
- **WHEN** the viewport width is at or below 720px
- **THEN** `compact-list` switches to a single-column layout (`grid-template-columns: 1fr`)
- **AND** baseline alignment and row spacing continue to produce a readable stacked layout

