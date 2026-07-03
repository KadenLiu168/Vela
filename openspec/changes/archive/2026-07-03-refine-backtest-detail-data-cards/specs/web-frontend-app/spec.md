## ADDED Requirements

### Requirement: Backtest Detail data dashboard card styling
The web frontend SHALL render the Backtest Detail metrics, equity curve, and parameters areas using the flat editorial data dashboard card visual language defined by `DESIGN.md` while preserving existing Backtest Detail behavior.

#### Scenario: Backtest metrics use editorial data cards
- **WHEN** the Backtest Detail route renders a successful backtest detail response
- **THEN** the metric card grid and metric cards MUST use tokenized neutral surfaces, borders, spacing, radii, and typography consistent with the data dashboard card system
- **AND** the rendered metric labels and formatted values remain unchanged

#### Scenario: Equity curve uses warm chart accent
- **WHEN** the Backtest Detail route renders a multi-point equity curve
- **THEN** the hand-written SVG chart remains present with `data-testid="equity-curve-line"`
- **AND** the equity curve stroke MUST use the `DESIGN.md` Ember or Brass accent token instead of a blue chart stroke
- **AND** the equity curve path calculation, API data usage, and chart summary values remain unchanged

#### Scenario: Equity curve empty and single-point states remain readable
- **WHEN** the Backtest Detail route renders no valid equity curve points or exactly one valid equity curve point
- **THEN** the existing empty or single-point message remains visible
- **AND** the surrounding surface, spacing, and summary details remain readable using tokenized Backtest Detail styling

#### Scenario: Parameters use readable tokenized surface
- **WHEN** the Backtest Detail route renders run parameters
- **THEN** the parameters block remains preformatted and horizontally scrollable when needed
- **AND** it uses tokenized neutral surfaces, borders, radius, typography, and spacing consistent with the surrounding Backtest Detail cards
