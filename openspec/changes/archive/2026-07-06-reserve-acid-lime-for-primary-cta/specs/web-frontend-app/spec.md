## MODIFIED Requirements

### Requirement: Bootstrap button uses primary visual variant
The web frontend SHALL render the "Bootstrap / Setup database &
data" Dashboard action in the primary (filled) button variant
and SHALL place it at the right end of the Dashboard action list.
The acid-lime reservation rule (added to the `design-system`
capability by this change) and the per-button variant className
contract (in `unify-buttons-into-three-variants`) jointly enforce
that no other Dashboard element except this Bootstrap button
renders an acid-lime filled background. Until those companion
changes land, this requirement pins Bootstrap as the designated
primary CTA; the visual enforcement is enforced by the next
OpenSpec change.

#### Scenario: Bootstrap is the rightmost Dashboard action
- **WHEN** the Dashboard renders its action list
- **THEN** the Bootstrap action MUST be the rightmost `<button>`
      element in the rendered list

#### Scenario: nav-link active state is not an acid-lime fill
- **WHEN** the user is on any route rendered through AppShell
- **THEN** the `.app-nav-link[aria-current="page"]` element MUST
      NOT use `var(--color-acid-lime)` as a `background`
- **AND** the active nav-link MAY use the lime as a 2px
      `box-shadow` inset underline or other non-fill decoration
- **AND** its text color MUST be `var(--color-paper)` resting
      and `var(--color-bone)` on `:hover`
