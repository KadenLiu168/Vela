## ADDED Requirements

### Requirement: Card heading 左右反转

The Dashboard card heading SHALL place the title (white, larger type) on the left as the primary reading anchor and the eyebrow (gray, smaller type) on the right as a secondary classification label.

The `PanelHeading` component SHALL make `eyebrow` optional; cards without an eyebrow SHALL render only the title and optional statusPill on the left.

#### Scenario: Market card heading is reversed

- **WHEN** the Dashboard renders the Market panel
- **THEN** the PanelHeading SHALL display `Market data` as the left-aligned title and `Price` as the right-aligned eyebrow

#### Scenario: Strategy card heading is reversed

- **WHEN** the Dashboard renders the Strategy panel
- **THEN** the PanelHeading SHALL display `Strategy` as the left-aligned title and `Config` as the right-aligned eyebrow

#### Scenario: Signal card omits eyebrow

- **WHEN** the Dashboard renders the Signal panel
- **THEN** the PanelHeading SHALL display `Latest signal` as the title with no eyebrow
- **AND** the statusPill SHALL remain adjacent to the title

#### Scenario: Backtest card omits eyebrow

- **WHEN** the Dashboard renders the Backtest panel
- **THEN** the PanelHeading SHALL display `Latest backtest` as the title with no eyebrow
- **AND** the statusPill SHALL remain adjacent to the title

#### Scenario: Fetches card omits eyebrow

- **WHEN** the Dashboard renders the Fetches panel
- **THEN** the PanelHeading SHALL display `Data fetches` as the title with no eyebrow
- **AND** the statusPill SHALL remain adjacent to the title
