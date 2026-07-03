## ADDED Requirements

### Requirement: Backtest detail equity curve ember highlights
The web frontend SHALL render restrained Ember Orange highlight points on Backtest Detail equity curve charts that contain two or more valid points, while retaining the Brass equity curve line.

#### Scenario: Multi-point equity curve shows ember highlight points
- **WHEN** the Backtest Detail API returns two or more valid equity curve rows with finite net values
- **THEN** the Backtest Detail page renders the existing equity curve line using `data-testid="equity-curve-line"`
- **AND** it renders small Ember Orange circle highlights for selected end or extreme points
- **AND** the highlights do not replace the Brass equity curve line

#### Scenario: Empty equity curve does not render highlights
- **WHEN** the Backtest Detail API returns no valid equity curve rows
- **THEN** the Backtest Detail page renders the empty equity curve state
- **AND** it does not render the equity curve line
- **AND** it does not render Ember Orange chart highlight points

#### Scenario: Single-point equity curve does not render chart highlights
- **WHEN** the Backtest Detail API returns exactly one valid equity curve row
- **THEN** the Backtest Detail page renders the single-point equity curve state
- **AND** it does not render the equity curve line
- **AND** it does not render Ember Orange chart highlight points
