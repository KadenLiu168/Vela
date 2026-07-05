## ADDED Requirements

### Requirement: Dashboard workflow panel visual cohesion
The web frontend SHALL render the Dashboard's bottom workflow row (`Signal`, `Backtest`, `Fetches` panels inside `.workflow-grid`) with a shared visual rhythm so the three panels read as one coordinated data strip.

#### Scenario: Each workflow panel uses a shared header shape
- **WHEN** the Dashboard renders a workflow panel for `Signal`, `Backtest`, or `Fetches`
- **THEN** the panel header contains three elements in order: an uppercase eyebrow label, a single-word h3 title, and a status pill aligned to the right of the header
- **AND** the h3 text is one of `Signal`, `Backtest`, or `Fetches` (the eyebrow provides full context such as `LATEST` or `HISTORY`)
- **AND** the h3 fits on a single line at the panel's column width at desktop, tablet, and mobile breakpoints

#### Scenario: Status pill reflects panel state without changing data
- **WHEN** the Dashboard renders a workflow panel
- **THEN** the panel header status pill is derived from the same data the panel body uses (loading state, present value, or absence of value)
- **AND** the pill uses one of the following variants mapped to existing color tokens: `success` (pulse-green), `partial` (signal-teal), `error` (coral-red), `neutral` (ash/graphite), `loading` (fog)
- **AND** the pill label is a short word from the set `Active`, `Partial`, `Errors`, `No data`, `Loading`
- **AND** the status pill is a presentation-only change and does not alter the API response, route, or data the panel already consumes

#### Scenario: Workflow panel empty states use a dashed-border treatment
- **WHEN** the Dashboard renders an empty state inside a `Signal`, `Backtest`, or `Fetches` panel
- **THEN** the empty state surface uses a 1px dashed border in `--color-graphite` on top of the panel's `var(--surface-obsidian)` background
- **AND** the empty state does not introduce a filled box darker than the panel
- **AND** the empty-state copy and the matching Dashboard action (or Operations control) continue to follow the existing `Empty workflow states point to matching actions` requirement
- **AND** other consumers of the shared `EmptyState` component outside the Dashboard workflow row are not affected

#### Scenario: Recent fetches renders compact two-row entries
- **WHEN** the Dashboard renders the `Fetches` panel with one or more recent fetch log summaries
- **THEN** each log entry is rendered as a compact two-row block: row 1 contains the fetch timestamp in monospace plus a status pill; row 2 contains the `Fetched / Inserted / Updated` row counts separated by middle dots
- **AND** the long error summary for an entry is collapsed by default behind a native disclosure control
- **AND** expanding the disclosure reveals the full `error_summary` text inline
- **AND** three or more entries fit within the existing `max-height: 320px; overflow-y: auto` boundary without stretching the panel row
- **AND** the panel header and primary value labels (fetch time, status) remain visible regardless of how many log entries are present

#### Scenario: Recent fetches scroll boundary keeps a thin styled scrollbar
- **WHEN** the `Fetches` panel's log list overflows the 320px boundary
- **THEN** the list scrolls inside the panel without expanding the row height
- **AND** the scrollbar is rendered with a thin, low-contrast treatment using existing tokens so it does not compete with the panel content
