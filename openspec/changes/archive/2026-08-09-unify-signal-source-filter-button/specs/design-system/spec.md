## ADDED Requirements

### Requirement: Secondary buttons render a selected state when pressed
A `button-secondary` button that carries `aria-pressed="true"` MUST render as selected with the inverted fill (`background: var(--color-mist)`, `color: var(--color-void)`, `border: 1px solid var(--color-mist)`). Single-select filter controls (e.g., the Signals SOURCE filter) are part of the three-variant button contract: every such `<button>` MUST carry exactly one variant className, and its visual treatment MUST come from the variant class rather than from a bespoke segmented style.

#### Scenario: pressed secondary button uses the inverted fill
- **WHEN** a `button-secondary` element has `aria-pressed="true"`
- **THEN** its `background` MUST be `var(--color-mist)`
- **AND** its `color` MUST be `var(--color-void)`
- **AND** its `border` MUST be `1px solid var(--color-mist)`

#### Scenario: selection controls declare a variant className
- **WHEN** a single-select filter control (e.g., the Signals SOURCE filter) renders its options as `<button>` elements
- **THEN** every such button MUST include exactly one of `button-primary`, `button-secondary`, or `button-tertiary` in its className
- **AND** its visual treatment MUST come from the declared variant class, not from a bespoke segmented style
- **AND** the selected option MUST be communicated via `aria-pressed="true"` and the inverted fill of the variant class
