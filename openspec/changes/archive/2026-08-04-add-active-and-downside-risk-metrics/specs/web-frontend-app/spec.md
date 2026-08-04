## ADDED Requirements

### Requirement: Backtest Detail presents expanded risk metrics with explicit semantics
Backtest Detail SHALL display persisted strategy Sortino, Calmar and longest drawdown duration. Each fixed benchmark group SHALL display its own Sortino, Calmar and duration plus strategy-relative Tracking Error and Information Ratio. Labels SHALL be `Sortino (rf MAR, 252D)`, `Calmar (calendar CAGR / |MaxDD|)`, `Tracking error (252D)`, and `Information ratio (252D)` or semantically equivalent text that exposes the same conventions.

#### Scenario: New run shows expanded metric groups
- **WHEN** a benchmark-enabled detail response contains expanded values
- **THEN** the Overview presents strategy and benchmark values under their correct semantic labels
- **AND** makes clear that TE/IR compare the strategy with the named benchmark

#### Scenario: Ongoing drawdown is explicit
- **WHEN** longest drawdown duration has a null recovery date
- **THEN** the detail shows duration sessions, peak and trough dates
- **AND** labels recovery as ongoing

#### Scenario: Legacy nulls do not fabricate metrics
- **WHEN** a legacy detail response has null expanded fields
- **THEN** the page renders the existing unavailable-value treatment
- **AND** does not derive values from the displayed curve

#### Scenario: Expanded groups remain readable across supported viewports
- **WHEN** Backtest Detail renders expanded strategy and benchmark groups at supported desktop and narrow viewport widths
- **THEN** metric labels, values and duration dates remain visible, correctly grouped and unclipped
- **AND** existing keyboard navigation and semantic ownership remain intact

### Requirement: Dashboard scope remains unchanged
The Dashboard summary SHALL continue to expose only its existing metric set and MUST NOT add expanded risk cards as part of this Change.

#### Scenario: Expanded detail does not expand Dashboard
- **WHEN** the Web application renders a newly completed run on Dashboard
- **THEN** no Sortino, Calmar, duration, Tracking Error or Information Ratio field is added there
