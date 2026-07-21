## MODIFIED Requirements

### Requirement: ETF price trend endpoint

The system SHALL expose `GET /api/etfs/{etf_id}/prices?range={1m|3m|1y|3y|max}` returning the forward-adjusted daily price series for one ETF over the requested horizon, derived from stored `market_price` rows at query time without persisting adjusted prices. The series SHALL be anchored at the latest persisted trade date selected for that request.

#### Scenario: Endpoint returns forward-adjusted daily series for a horizon
- **WHEN** a client requests `GET /api/etfs/{etf_id}/prices?range=1y` for an ETF with persisted market prices
- **THEN** the response status is 200
- **AND** the response body includes an `etf` object with `id`, `exchange`, `symbol`, and `name`
- **AND** the response body includes a `points` array ordered by `trade_date` ascending
- **AND** each point price equals `close_price * factor_hfq / factor_hfq(T)`, where `T` is the latest selected trade date
- **AND** the point for `T` equals its unadjusted `close_price`

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

### Requirement: ETF trend chart interaction

The trend chart SHALL render the forward-adjusted price series returned by the endpoint as a line without applying a second adjustment. It SHALL surface per-point readout on hover. Hover SHALL resolve to the data point whose x-coordinate is nearest the pointer, clamped to the series bounds, so the highlighted point tracks the cursor without band-cell misalignment. Hover hit detection SHALL be served by a single overlay element covering the plot area rather than one interactive element per data point, so interaction cost does not grow with series length.

#### Scenario: Chart renders forward-adjusted line with axis labels
- **WHEN** the series has two or more points
- **THEN** the chart renders a line path through the returned forward-adjusted point values without applying a second adjustment
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
