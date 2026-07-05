## ADDED Requirements

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
