## ADDED Requirements

### Requirement: EmptyAction advertises its variant
The Dashboard's component-level `EmptyAction` function MUST
accept a `variant` prop and MUST render the matching
`.button-{primary,secondary,tertiary}` className on its
inner `<button>` element, satisfying the "Buttons declare
their variant via className" rule in the `design-system`
capability.

#### Scenario: EmptyAction accepts a variant prop
- **WHEN** a developer reads the `EmptyAction` function
      signature in `apps/web/src/pages/DashboardPage.tsx`
- **THEN** its parameter list MUST include a `variant`
      parameter typed as one of the three literal strings
      `"button-primary"`, `"button-secondary"`, or
      `"button-tertiary"`
- **AND** the parameter MUST default to `"button-secondary"`
      so existing call sites without an explicit `variant`
      prop render exactly as they do today

#### Scenario: EmptyAction renders the variant className
- **WHEN** the `EmptyAction` function returns its JSX
- **THEN** the rendered `<button>` element's `className`
      MUST be the value of the `variant` prop (verbatim),
      not the hardcoded literal `"button-secondary"`
- **AND** the rendered DOM MUST therefore carry a variant
      class that satisfies the `design-system` capability's
      "Buttons declare their variant via className"
      Requirement

#### Scenario: existing call sites continue to render a secondary button
- **WHEN** `EmptyAction` is invoked without an explicit
      `variant` prop (the two existing call sites in
      `DashboardPage.tsx`)
- **THEN** the rendered `<button>` carries
      `className="button-secondary"`
- **AND** the visual outcome is byte-identical to the
      pre-change render of those two call sites
