## MODIFIED Requirements

### Requirement: Current-state layer offers the next research action
The current-state layer SHALL name at most one next research action and SHALL offer it as a control that moves focus to the pre-existing Dashboard control for that action rather than duplicating its trigger. The action SHALL be selected only from these conditions, in this priority order: no market data is stored, no successful signal exists, or the latest signal lags the market-data cutoff. A backtest whose range ends before the market-data cutoff SHALL be reported as a lagging fact but SHALL NOT on its own select an action, because an evaluation window is a deliberate research choice. The offered control SHALL NOT be the view's primary CTA.

#### Scenario: Action targets the missing artifact
- **WHEN** market data exists but no successful signal exists for the current strategy and config version
- **THEN** the layer offers exactly one next action that leads to signal generation
- **AND** it does not offer a market-data fetch as the same next action

#### Scenario: Action control is not the primary CTA
- **WHEN** the current-state layer renders its next-action control
- **THEN** the control does not use the shared primary fill
- **AND** the Dashboard's existing Bootstrap action remains the only prominent primary CTA, using the semantic interaction treatment

#### Scenario: A lagging backtest alone selects no action
- **WHEN** market data and a current latest signal exist and a backtest exists whose range ends before the market-data cutoff
- **THEN** the layer still reports that backtest range as lagging
- **AND** it offers no corrective action for it

#### Scenario: The no-action message claims only what the facts support
- **WHEN** the layer offers no corrective action while an artifact is displayed as lagging
- **THEN** the message SHALL NOT state that the lagging artifact is current
- **AND** it SHALL limit its claim to the artifacts it can support, or state only that no corrective action is needed

### Requirement: Decision layers are responsive, keyboard accessible, and non-overflowing
Every decision layer SHALL use shared design tokens, SHALL remain keyboard operable with programmatically associated labels, and SHALL NOT cause page-level horizontal overflow at 1440x1000 or 390x844. A dense holdings table MAY use a labeled local scroll region.

#### Scenario: Narrow viewport keeps the decision path usable
- **WHEN** the Dashboard renders at 390x844
- **THEN** all five decision layers remain readable in order
- **AND** no page-level horizontal overflow occurs outside a labeled local table region
- **AND** every link and control remains reachable by keyboard

#### Scenario: Decision layers reuse the design system
- **WHEN** the decision layers render
- **THEN** no new button variant, no primary filled button beyond the view's primary CTA, and no non-token line-height is introduced
