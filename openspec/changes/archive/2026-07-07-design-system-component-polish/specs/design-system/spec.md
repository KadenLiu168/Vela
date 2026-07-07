## ADDED Requirements

### Requirement: Radius → component mapping is canonical
The web frontend MUST follow a documented mapping between each
component family and a single radius token. The mapping is:

- **Card** (`.panel-primary`, `.dashboard-card`, `.metric-card`,
  and similar surfaces) → `var(--radius-cards)` (12 px)
- **Button** (`.button-primary`, `.button-secondary`,
  `.button-tertiary`) → `var(--radius-buttons)` (6 px)
- **Input** (`input`, `select`, `textarea`) →
  `var(--radius-inputs)` (6 px)
- **Badge** (numeric / status badges) →
  `var(--radius-badges)` (4 px)
- **Navigation chrome** (`.app-nav`, `.app-nav-link`) →
  `var(--radius-md)` (6 px). Navigation chrome is NOT a pill.
- **Pill** (true pill-shaped chrome: `--radius-pills: 9999px`)
  is reserved for badge / tag components and MUST NOT be used
  on navigation chrome

Components not in this list SHOULD consume the closest primitive
(`--radius-sm` 2 px, `--radius-md` 6 px, `--radius-xl` 12 px,
`--radius-2xl` 16 px) and document the choice in their CSS rule.

#### Scenario: navigation chrome is not a pill
- **WHEN** `apps/web/src/styles.css` is searched for the
      `.app-nav-link` rule
- **THEN** its `border-radius` MUST resolve to `var(--radius-md)`
      (or any non-pill radius token — `--radius-sm`,
      `--radius-md`, `--radius-buttons`, `--radius-cards`)
- **AND** it MUST NOT resolve to `var(--radius-pills)` or
      `var(--radius-full)` or `var(--radius-full-2)`

#### Scenario: nav container is not a pill
- **WHEN** `apps/web/src/styles.css` is searched for the
      `.app-nav` rule
- **THEN** its `border-radius` MUST resolve to a non-pill
      radius token (`--radius-sm`, `--radius-md`,
      `--radius-buttons`, `--radius-cards`)
- **AND** it MUST NOT resolve to `var(--radius-pills)` or
      `var(--radius-full)` or `var(--radius-full-2)`

#### Scenario: button rules use --radius-buttons
- **WHEN** any CSS rule under `apps/web/src/styles.css` styles
      a `.button-primary`, `.button-secondary`, or
      `.button-tertiary` element
- **THEN** its `border-radius` MUST come from
      `var(--radius-buttons)`

#### Scenario: card surfaces use --radius-cards
- **WHEN** any CSS rule under `apps/web/src/styles.css` styles
      a card surface (`.panel-primary`, `.dashboard-card`,
      `.metric-card`, `.equity-curve-card`, or analogous
      surface)
- **THEN** its `border-radius` MUST come from
      `var(--radius-cards)`

### Requirement: Dashboard heading uses a discrete responsive ladder
The web frontend MUST render the Dashboard page heading
(`.dashboard-heading h1`) at one of three discrete sizes — 48,
64, or 72 px — based on viewport width:

- Viewport `< 768 px`: `var(--text-heading)` (48 px)
- Viewport `>= 768 px` and `< 1280 px`: `var(--text-heading-lg)`
  (64 px)
- Viewport `>= 1280 px`: `var(--text-display)` (72 px)

The transition between sizes MUST be a discrete step at the
named breakpoint, not a fluid `clamp()` ramp.

#### Scenario: dashboard heading has three discrete sizes
- **WHEN** `apps/web/src/styles.css` is searched for the
      `.dashboard-heading h1` rule
- **THEN** it MUST contain a base `font-size` resolving to
      `var(--text-heading)` (48 px) for the default viewport
- **AND** it MUST contain a `@media (min-width: 768px)` block
      that sets `font-size: var(--text-heading-lg)` (64 px)
- **AND** it MUST contain a `@media (min-width: 1280px)` block
      that sets `font-size: var(--text-display)` (72 px)
- **AND** it MUST NOT contain a `clamp(...)` value for `font-size`

#### Scenario: mobile override does not contradict the ladder
- **WHEN** `apps/web/src/styles.css` is searched for any
      `@media` block that targets `.dashboard-heading h1`
- **THEN** the `@media` block MUST NOT re-pin the heading to
      `var(--text-heading)` at a viewport where the ladder
      would already produce `var(--text-heading-lg)` or
      `var(--text-display)`
