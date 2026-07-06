## ADDED Requirements

### Requirement: Acid-lime is reserved for the per-view primary CTA
The acid-lime fill MUST appear at most once in any rendered view.
The lime fill is the visual marker reserved for the per-view primary
CTA and MUST NOT be applied to more than one button-shaped element in
the same rendered view. That one use is the primary
CTA of the view; all other buttons in the same view MUST use the
secondary (outline / ghost) or tertiary (text-only) variant.

Non-button uses of lime (e.g. as a hairline underline, as a
focus-ring color) do not consume the reservation.

#### Scenario: nav active state uses lime only as an underline
- **WHEN** an `<a className="app-nav-link">` carries
      `aria-current="page"` (the nav active state)
- **THEN** its `background` MUST NOT be `var(--color-acid-lime)`
- **AND** its underline / hairline accent MAY use the lime
      (e.g. `box-shadow: inset 0 -2px 0 0 var(--color-acid-lime);`)
- **AND** its text color MUST be `var(--color-paper)` (resting)
      or `var(--color-bone)` (hover)

#### Scenario: only one button per view may be filled lime
- **WHEN** any rendered view of the web frontend contains two or
      more elements styled with
      `background: var(--color-acid-lime)`
      AND each is visually a button
- **THEN** the change that introduced the second such element is
      non-conforming with this capability
- **AND** the second button MUST be reclassified as secondary or
      tertiary
