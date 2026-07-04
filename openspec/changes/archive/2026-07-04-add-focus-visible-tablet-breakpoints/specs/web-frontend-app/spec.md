## ADDED Requirements

### Requirement: Web frontend keyboard focus visibility
The web frontend SHALL provide a clear visible focus indicator for keyboard-focused interactive controls, including links, buttons, navigation entries, and form inputs.

#### Scenario: Keyboard focus is visible on interactive controls
- **WHEN** a user tabs through Dashboard, Signal Detail, and Backtest Detail controls
- **THEN** each focused link, button, navigation entry, and input shows a clear focus ring
- **AND** the focus ring uses outline-based styling instead of box-shadow-based styling

#### Scenario: Focus styling preserves disabled control semantics
- **WHEN** an action button or form control is disabled
- **THEN** the control remains visibly disabled
- **AND** the frontend does not add hover or focus affordances that imply the disabled control is actionable

### Requirement: Web frontend restrained interaction motion
The web frontend SHALL keep hover and transition feedback restrained and SHALL respect reduced-motion user preferences.

#### Scenario: Hover feedback does not shift layout
- **WHEN** a pointer hovers over an enabled interactive control
- **THEN** the feedback is limited to subtle color, background, border, or text-decoration changes
- **AND** the control does not bounce, translate, scale, or otherwise visibly move

#### Scenario: Reduced motion disables nonessential transitions
- **WHEN** the user has `prefers-reduced-motion: reduce`
- **THEN** nonessential CSS transitions for interactive controls are disabled

### Requirement: Web frontend tablet and small-desktop responsive layouts
The web frontend SHALL provide intermediate responsive layout rules between the desktop layout and the existing `720px` mobile layout.

#### Scenario: Dashboard remains stable at tablet widths
- **WHEN** the Dashboard is viewed around `900px` or `1024px` viewport width
- **THEN** the dashboard grid, metric rows, and operations area fit without obvious crowding or horizontal page overflow
- **AND** the layout preserves the existing single-column behavior below `720px`

#### Scenario: Signal Detail remains stable at tablet widths
- **WHEN** the Signal Detail page is viewed around `900px` or `1024px` viewport width
- **THEN** the metadata block and target holdings table container fit within the page without causing horizontal page overflow
- **AND** any table overflow remains contained within the table scroll container

#### Scenario: Backtest Detail remains stable at tablet widths
- **WHEN** the Backtest Detail page is viewed around `900px` or `1024px` viewport width
- **THEN** metric cards, equity curve content, equity summary, and parameter summary fit without obvious crowding or horizontal page overflow
- **AND** the layout preserves the existing desktop behavior at `1200px` and above
