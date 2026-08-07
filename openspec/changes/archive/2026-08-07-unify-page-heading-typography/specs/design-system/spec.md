# design-system (delta)

## MODIFIED Requirements

### Requirement: Dashboard heading uses a discrete responsive ladder

The web frontend MUST render the page heading (`page-heading h1`) on every page
using a single shared type scale: `font-size: var(--text-heading-sm)` (32 px),
`letter-spacing: var(--tracking-heading-sm)`, `line-height: var(--leading-heading-sm)`,
and `font-weight: var(--font-weight-medium)`.

The Dashboard heading MUST NOT carry a separate type override: the
`.dashboard-heading h1` rule MUST NOT redeclare `font-size`, `letter-spacing`,
or `line-height` with values that differ from the shared `page-heading h1` base
rule. Layout properties of `.dashboard-heading` (flex alignment, gap, max-width)
are unaffected.

#### Scenario: all pages share one heading type scale

- **WHEN** `apps/web/src/styles.css` is searched for the `page-heading h1` rule
- **THEN** its `font-size` resolves to `var(--text-heading-sm)` (32 px)
- **AND** its `letter-spacing` resolves to `var(--tracking-heading-sm)`
- **AND** its `line-height` resolves to `var(--leading-heading-sm)`
- **AND** it does not contain a `clamp(...)` value for `font-size`

#### Scenario: dashboard heading has no divergent override

- **WHEN** `apps/web/src/styles.css` is searched for the `.dashboard-heading h1` rule
- **THEN** it MUST NOT redeclare `font-size`, `letter-spacing`, or `line-height`
      with values that differ from the shared `page-heading h1` base rule
- **AND** any existing `.dashboard-heading h1` type declarations MAY be absent
      entirely, leaving the base rule to apply

#### Scenario: mobile media query does not reintroduce a larger size

- **WHEN** `apps/web/src/styles.css` is searched for any `@media` block that
      targets `.page-heading h1` or `.dashboard-heading h1`
- **THEN** the `@media` block MUST NOT set `font-size` to a value other than
      `var(--text-heading-sm)` for the shared heading
