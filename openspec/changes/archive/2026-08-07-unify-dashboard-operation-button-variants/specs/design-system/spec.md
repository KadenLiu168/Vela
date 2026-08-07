# design-system (delta)

## MODIFIED Requirements

### Requirement: Buttons follow a three-variant contract

Every button in the web frontend MUST be exactly one of three
variants: `primary` (filled accent), `secondary` (outline / ghost),
or `tertiary` (text-only). A fourth visual treatment MUST NOT be
introduced without a new OpenSpec change. Buttons appearing inside
the same operation group (`.operation-list`) MUST use the same
visual tier (`secondary`) so the group reads as one coherent set;
only a view-level primary CTA MAY use the `primary` tier within
such a group.

#### Scenario: primary button uses the accent fill
- **WHEN** a button declares the `primary` variant
- **THEN** its `background` MUST be `var(--color-acid-lime)`
- **AND** its `color` MUST be `var(--color-void)`
- **AND** its `border-radius` MUST be `var(--radius-md)`
- **AND** no other button in the same view MAY use the accent fill
      (the acid-lime button is the sole chromatic UI element per view)

#### Scenario: secondary button is outline-only
- **WHEN** a button declares the `secondary` variant
- **THEN** its `background` MUST be `transparent`
- **AND** its `border` MUST be
      `1px solid var(--color-graphite)` (or `var(--color-smoke)`
      at higher contrast)
- **AND** its `color` MUST be `var(--color-mist)`

#### Scenario: tertiary button is text-only
- **WHEN** a button declares the `tertiary` variant
- **THEN** it MUST have neither background nor border
- **AND** its `color` MUST be `var(--color-mist)` resting and
      `var(--color-paper)` on `:hover`

#### Scenario: buttons in one operation group share a tier
- **WHEN** two or more buttons render inside the same
      `.operation-list` group
- **THEN** every button in the group MUST use the `secondary`
      variant unless it is the view-level primary CTA
- **AND** no button in the group MUST use the `tertiary`
      (text-only) variant while a sibling uses `secondary`
