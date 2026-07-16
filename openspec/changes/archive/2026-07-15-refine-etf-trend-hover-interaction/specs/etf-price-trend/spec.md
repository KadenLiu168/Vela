## MODIFIED Requirements

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
