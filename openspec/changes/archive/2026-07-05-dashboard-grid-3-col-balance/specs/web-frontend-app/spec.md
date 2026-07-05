## ADDED Requirements

### Requirement: Dashboard desktop grid layout
The web frontend SHALL render the desktop Dashboard (`/`) using a 3-column equal-width grid track layout such that the three workflow panels in the bottom row (Signal, Backtest, Fetches) each occupy one column with no trailing empty column slot.

#### Scenario: Desktop bottom row has no trailing whitespace
- **WHEN** the Dashboard renders populated workflow data at a viewport width above the existing 1024px responsive breakpoint
- **THEN** the grid uses 3 equal columns
- **AND** `.signal-panel`, `.backtest-panel`, and `.fetch-log-panel` each span exactly 1 column
- **AND** no column slot in the bottom row is empty

#### Scenario: Operations panel still spans the full row
- **WHEN** the Dashboard renders at a desktop viewport width
- **THEN** `.operations-panel` spans all 3 grid columns so it remains visually a full-width action bar

#### Scenario: Top row redistributes cleanly into 3 columns
- **WHEN** the Dashboard renders at a desktop viewport width
- **THEN** the top row is filled by `.market-panel` and `.strategy-panel` whose `grid-column` spans sum to 3
- **AND** the chosen distribution keeps the denser panel (`.strategy-panel`) at the wider span

#### Scenario: Responsive breakpoints are unchanged
- **WHEN** the Dashboard renders at or below the existing 1024px and 720px breakpoints
- **THEN** those breakpoints continue to apply the 2-column and 1-column layouts defined in `apps/web/src/styles.css`
- **AND** this requirement does not introduce new responsive behavior
