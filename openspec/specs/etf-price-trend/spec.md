# etf-price-trend Specification

## Purpose
TBD - created by archiving change add-etf-price-trend-chart. Update Purpose after archive.
## Requirements
### Requirement: ETF price trend endpoint
The system SHALL expose `GET /api/etfs/{etf_id}/prices?range={1m|3m|1y|3y|max}` returning the backward-adjusted daily price series for one ETF over the requested horizon, derived from stored `market_price` rows at query time without persisting adjusted prices.

#### Scenario: Endpoint returns backward-adjusted daily series for a horizon
- **WHEN** a client requests `GET /api/etfs/{etf_id}/prices?range=1y` for an ETF with persisted market prices
- **THEN** the response status is 200
- **AND** the response body includes an `etf` object with `id`, `exchange`, `symbol`, and `name`
- **AND** the response body includes a `points` array ordered by `trade_date` ascending
- **AND** each point includes `trade_date` (ISO date) and `price` where `price` equals `close_price * factor_hfq` for that row

#### Scenario: Endpoint resolves range to a date window anchored at the ETF's latest trade date
- **WHEN** a client requests `range=3m` for an ETF with persisted prices
- **THEN** the series start date is the latest persisted `trade_date` for that ETF shifted back 3 calendar months
- **AND** the series end date is the latest persisted `trade_date` for that ETF
- **AND** only rows with `trade_date` within the window are included

#### Scenario: range=max returns the full persisted history
- **WHEN** a client requests `range=max`
- **THEN** no start-date lower bound is applied
- **AND** the series includes every persisted `market_price` row for that ETF ordered ascending

#### Scenario: Unknown etf_id returns 404
- **WHEN** a client requests an `etf_id` for which no `ETFInfo` row exists
- **THEN** the response status is 404
- **AND** the response body uses the stable API error shape with category `not_found`

#### Scenario: ETF with no persisted prices returns empty points
- **WHEN** a client requests a range for an ETF that exists but has no `market_price` rows
- **THEN** the response status is 200
- **AND** the `points` array is empty
- **AND** the `etf` object is still populated

#### Scenario: Invalid range value returns validation error
- **WHEN** a client requests `range=2y` (a value outside the allowed set)
- **THEN** the response status is 422
- **AND** the response body uses the stable API error shape with category `validation`

### Requirement: ETF trend page horizon switching
The web frontend SHALL render an ETF trend detail page at route `/etfs/{etf_id}` that loads the price series for a selected horizon and re-fetches when the horizon changes.

#### Scenario: Page loads default horizon
- **WHEN** the user navigates to `/etfs/{etf_id}`
- **THEN** the frontend requests `GET /api/etfs/{etf_id}/prices?range=1y`
- **AND** the page renders the ETF identity and the trend chart for the returned series

#### Scenario: User switches horizon
- **WHEN** the user selects a different horizon control (`1M`, `3M`, `1Y`, `3Y`, `Max`)
- **THEN** the frontend requests the price series for the new range
- **AND** the chart re-renders with the new series

#### Scenario: Unknown etf_id renders not-found state
- **WHEN** the price-series request returns 404
- **THEN** the page renders a not-found state instead of the chart

#### Scenario: Loading and error states
- **WHEN** a price-series request is in flight or fails
- **THEN** the page renders a loading or error feedback state consistent with the other detail pages

### Requirement: ETF trend chart interaction
The trend chart SHALL render the backward-adjusted price series as a line and SHALL surface per-point readout on hover. Hover SHALL resolve to the data point whose x-coordinate is nearest the pointer, clamped to the series bounds, so the highlighted point tracks the cursor without band-cell misalignment. Hover hit detection SHALL be served by a single overlay element covering the plot area rather than one interactive element per data point, so interaction cost does not grow with series length.

#### Scenario: Chart renders line with axis labels
- **WHEN** the series has two or more points
- **THEN** the chart renders a line path through the points
- **AND** the chart displays date axis labels spanning the series range
- **AND** the chart displays price axis labels spanning the series min and max

#### Scenario: Hover resolves to the nearest point by x-coordinate
- **WHEN** the user moves the pointer within the chart plot area
- **THEN** the chart resolves hover to the data point whose x-coordinate is nearest the pointer's x-coordinate
- **AND** the resolved index is clamped to `[0, pointCount - 1]` at the plot edges
- **AND** the readout displays that point's `trade_date` and `price`
- **AND** the highlighted marker aligns with the resolved point directly under the cursor, with no half-cell offset between the pointer and the highlighted point

#### Scenario: Hover clears on pointer leave
- **WHEN** the pointer leaves the chart plot area
- **THEN** the chart clears the hover selection
- **AND** the readout reflects the series' latest point

#### Scenario: Hover hit detection is independent of point count
- **WHEN** the chart renders a series of any length with two or more points
- **THEN** hover hit detection is served by a single overlay element covering the plot area
- **AND** there is not one interactive hover element per data point

#### Scenario: Single point series
- **WHEN** the series has exactly one point
- **THEN** the chart renders a single-point state without a line path

#### Scenario: Empty series
- **WHEN** the series has zero points
- **THEN** the chart renders an empty state

### Requirement: Dashboard ETF row links to trend detail
The web frontend Dashboard SHALL render an entry control on each `etf-row` that navigates to that ETF's trend detail page using the `etf_id` from the Dashboard aggregate.

#### Scenario: etf-row navigates to trend detail
- **WHEN** the user activates the detail entry control on a Dashboard `etf_row`
- **THEN** the frontend navigates to `/etfs/{etf_id}` using that row's `etf_id`

#### Scenario: etf-row renders entry control only when etf_id is present
- **WHEN** the Dashboard aggregate returns an `etf_list` entry without `etf_id`
- **THEN** the detail entry control is not rendered for that row

