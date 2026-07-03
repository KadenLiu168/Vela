## ADDED Requirements

### Requirement: Dashboard action and feedback styling follows design tokens
The web frontend SHALL render Dashboard operation actions, empty-state action buttons, Backtest run form controls, load states, alerts, operation summaries, operation guidance, and operation links using the project design-token visual language.

#### Scenario: Dashboard actions use Graphite action dialects
- **WHEN** the Dashboard renders operation buttons, empty-state action buttons, and the refresh action
- **THEN** the actions use 0px button radius
- **AND** filled actions use Graphite backgrounds instead of Ember Orange backgrounds
- **AND** outlined actions use tokenized Graphite, Mist, Canvas, Fog, and typography values

#### Scenario: Backtest form controls use tokens
- **WHEN** the Dashboard renders the Backtest run date inputs
- **THEN** the controls use tokenized border, background, color, typography, spacing, and 0px control radius values

#### Scenario: Operation feedback avoids broad chromatic blocks
- **WHEN** Dashboard loading, error, success, partial, failed, and validation feedback is visible
- **THEN** the feedback uses neutral tokenized surfaces and borders with narrow Ember or Brass accents
- **AND** broad blue, green, or red filled feedback blocks are not used

#### Scenario: Dashboard operation behavior is preserved
- **WHEN** Dashboard operation buttons, Backtest validation feedback, loading feedback, error feedback, and operation summaries render
- **THEN** existing button enabled, disabled, and loading conditions remain unchanged
- **AND** existing API calls, routing targets, form validation logic, and `role="status"` or `role="alert"` accessibility semantics remain unchanged
