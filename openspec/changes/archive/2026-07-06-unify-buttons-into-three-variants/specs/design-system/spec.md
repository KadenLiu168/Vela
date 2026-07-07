## ADDED Requirements

### Requirement: Buttons declare their variant via className
Every `<button>` (or `[role="button"]`) in `apps/web/src/` MUST
carry a className of the exact form `button-primary`,
`button-secondary`, or `button-tertiary` to advertise its variant
to CSS and tooling. The visual treatment carried by each class
is the one declared under "Buttons follow a three-variant
contract" in the `design-system` capability.

#### Scenario: every styled button has a variant className
- **WHEN** any HTML element under `apps/web/src/` carries the role
      of an actionable button (`<button>`, `[role="button"]`,
      `<input type="button">`, `<input type="submit">`)
- **THEN** its className MUST include one of the literal class
      tokens `button-primary`, `button-secondary`, or
      `button-tertiary`
- **AND** it MUST NOT include more than one variant class

#### Scenario: variant class is the only carrier of visual treatment
- **WHEN** a CSS rule under `apps/web/src/styles.css` declares a
      visual property for buttons (background, color, border,
      box-shadow, or font-weight)
- **THEN** the rule's selector MUST begin with one of the three
      `.button-primary`, `.button-secondary`, `.button-tertiary`
      class selectors (or a documented descendant of one of them)
- **AND** no rule MUST select buttons by ancestry alone
      (e.g. `.operation-list button`)

#### Scenario: third-party buttons get a variant too
- **WHEN** any third-party component (e.g. `EmptyAction`,
      `FeedbackMessage`) renders a button on behalf of the web
      frontend
- **THEN** the rendered DOM MUST include the appropriate variant
      className on the button (either inside the component or at
      the call site)
