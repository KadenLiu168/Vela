## ADDED Requirements

### Requirement: Editorial research page hierarchy
The web frontend SHALL render the Dashboard, Signal Detail, and Backtest Detail page skeletons with editorial spacing, clear page-heading hierarchy, and a restrained asymmetric featured card using the existing design tokens.

#### Scenario: Research pages use editorial spacing tokens
- **WHEN** a developer inspects the active web stylesheet for the Dashboard, Signal Detail, and Backtest Detail page skeletons
- **THEN** page-level section spacing uses the existing `--section-gap` token
- **AND** prominent page or card containers use the existing `--card-padding` token

#### Scenario: Page headings have clear hierarchy
- **WHEN** a user opens the Dashboard, Signal Detail, or Backtest Detail page
- **THEN** the page heading presents an eyebrow followed by the page title
- **AND** the page title uses either `--text-heading-lg` or `--text-display`
- **AND** the title font weight remains 400

#### Scenario: Dashboard remains an internal research tool
- **WHEN** a user opens the Dashboard route
- **THEN** the first screen remains focused on local workflow status and data panels
- **AND** it does not introduce marketing hero copy, decorative hero artwork, or CTA button clusters

#### Scenario: Signature asymmetric card is restrained
- **WHEN** a developer inspects the active web stylesheet
- **THEN** at least one featured guidance block uses `--radius-asymmetric-card`
- **AND** ordinary dashboard data panels do not use the asymmetric radius

#### Scenario: Mobile page skeleton remains usable
- **WHEN** the viewport is below 720px wide
- **THEN** the Dashboard, Signal Detail, and Backtest Detail page skeletons continue to stack content without horizontal layout regression from editorial spacing or card padding
