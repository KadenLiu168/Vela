# design-system Specification

## Purpose
TBD - created by archiving change add-design-system-spec. Update Purpose after archive.
## Requirements
### Requirement: Design tokens live in a single canonical file

The canonical on-disk source of design tokens for the web frontend MUST be
`apps/web/src/styles/tokens.css`. The file MUST be a single
`:root { ... }` block declaring every CSS custom property the web
frontend uses as a design token (color, surface, typography, spacing,
radius, shadow, layout, or feedback accent).

#### Scenario: tokens.css is imported by the stylesheet
- **WHEN** the web app builds
- **THEN** `apps/web/src/styles.css` MUST contain
      `@import "./tokens.css";` (resolved relative to
      `apps/web/src/styles/`) at the top of the file
- **AND** `apps/web/src/styles.css` MUST NOT contain a
      `:root { ... }` block
- **AND** every other `.css` file under `apps/web/src/` MUST NOT
      contain a `:root { ... }` block

#### Scenario: introducing a competing token declaration is non-conforming
- **WHEN** any CSS file under `apps/web/src/` (other than
      `tokens.css`) declares a CSS custom property inside a
      `:root { ... }` block
- **THEN** the change that introduces that declaration is
      non-conforming with this capability

#### Scenario: token catalog is the documented source of truth
- **WHEN** a developer needs to know whether a CSS variable exists
      or what role it plays
- **THEN** they SHOULD read `apps/web/src/styles/tokens.css` first
- **AND** the file MUST contain a leading comment block listing the
      token groups it declares (Colors, Surfaces, Typography,
      Spacing, Radius, Shadow, Feedback accents, Layout, Motion)

### Requirement: Monospace font token name follows design intent

The monospace font token MUST be named after the design intent
(Berkeley Mono in the Linear reference system), not after the OFL
substitute loaded at runtime.

#### Scenario: token name is --font-berkeley-mono
- **WHEN** `tokens.css` declares the monospace family token
- **THEN** the token name MUST be `--font-berkeley-mono`
- **AND** the value MUST chain
      `'JetBrains Mono', 'Berkeley Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`
      in that exact order
- **AND** the value's first entry (`'JetBrains Mono'`) MUST match
      the `font-family` declared by the `@font-face` rule for the
      JetBrains Mono woff2 in `apps/web/src/styles.css`

#### Scenario: every consumer uses the canonical token name
- **WHEN** any CSS rule under `apps/web/src/` references the
      monospace family token
- **THEN** the reference MUST use `var(--font-berkeley-mono)`
- **AND** no CSS rule MUST use `var(--font-jetbrains-mono)`

### Requirement: Implementation-only tokens live in tokens.css

The implementation-only tokens listed below MUST live in `tokens.css`
(today they are declared only inside `apps/web/src/styles.css :root`):
`--text-micro`, `--text-label`, `--text-body`, `--leading-body`,
every `--feedback-accent-*` (`--feedback-accent`,
`--feedback-accent-loading`, `--feedback-accent-success`,
`--feedback-accent-error`, `--feedback-accent-info`,
`--feedback-accent-empty`), `--focus-ring-color`, `--radius-cards`,
`--radius-pills`, and `--surface-slate`.

#### Scenario: feedback accents resolve to the named palette tokens
- **WHEN** any UI element signals feedback (loading, success, error,
      info, or empty state)
- **THEN** its accent color MUST come from one of
      `var(--feedback-accent-loading)`,
      `var(--feedback-accent-success)`,
      `var(--feedback-accent-error)`,
      `var(--feedback-accent-info)`, or
      `var(--feedback-accent-empty)`
- **AND** each of those tokens MUST resolve to one of:
      `var(--color-acid-lime)`,
      `var(--color-pulse-green)`,
      `var(--color-coral-red)`,
      `var(--color-signal-teal)`, or
      `var(--color-smoke)`

#### Scenario: focus ring uses --focus-ring-color
- **WHEN** an element receives `:focus-visible`
- **THEN** its outline color MUST come from
      `var(--focus-ring-color)`
- **AND** `var(--focus-ring-color)` MUST resolve to
      `var(--color-acid-lime)`

#### Scenario: card and pill radii use the named aliases
- **WHEN** a card element renders
- **THEN** its `border-radius` MUST come from
      `var(--radius-cards)` (which MUST resolve to `12px`)
- **WHEN** a pill element renders
- **THEN** its `border-radius` MUST come from
      `var(--radius-pills)` (which MUST resolve to `9999px`)

### Requirement: Token and component changes flow through OpenSpec

Token and component contract changes MUST be made through an OpenSpec
change proposal that updates this spec. The MUST-cover range is any
addition, removal, rename, or value change of a CSS custom property
declared in `apps/web/src/styles/tokens.css`, or any addition or removal
of a contract documented in this capability.

#### Scenario: adding a new token requires an OpenSpec change
- **WHEN** a developer needs a CSS variable that does not yet exist
      in `tokens.css`
- **THEN** they MUST open a change under `openspec/changes/` that
      declares the new token's name, value, and role, and lists
      every consumer the token will replace or augment
- **AND** the change MUST be archived (via `openspec-archive-change`)
      before the token appears in `tokens.css`

#### Scenario: renaming a token requires a same-change migration
- **WHEN** an existing token name is changed
- **THEN** the OpenSpec change MUST list every `var(<old-name>)`
      call site under `apps/web/src/` that is renamed in the same
      commit
- **AND** the old name MUST NOT remain in `tokens.css` after the
      change archives

### Requirement: Buttons follow a three-variant contract

Every button in the web frontend MUST be exactly one of three
variants: `primary` (filled accent), `secondary` (outline / ghost),
or `tertiary` (text-only). A fourth visual treatment MUST NOT be
introduced without a new OpenSpec change.

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

### Requirement: Motion vocabulary is declared and respected

The web frontend MUST declare a motion vocabulary in `tokens.css`
(durations and easings) and MUST honor the user's
`prefers-reduced-motion` setting.

#### Scenario: durations and easings live in tokens.css
- **WHEN** any CSS rule under `apps/web/src/` declares a
      `transition` or `animation`
- **THEN** the duration MUST come from one of `--duration-fast`
      (120ms), `--duration-base` (200ms), or `--duration-slow`
      (320ms)
- **AND** the easing MUST be `cubic-bezier(0.2, 0, 0, 1)` declared
      as `--ease-out` unless a different named token documents a
      specific need

#### Scenario: prefers-reduced-motion suppresses non-essential motion
- **WHEN** the OS reports `prefers-reduced-motion: reduce`
- **THEN** a global media query in `apps/web/src/styles.css` MUST
      set `transition-duration: 0ms` and `animation-duration: 0ms`
      on every element that uses a motion token
- **AND** non-essential motion MUST be suppressed; loading spinners
      driven by user-initiated actions MAY remain

### Requirement: Line-height MUST come from a `--leading-*` token
Any `line-height` declaration under `apps/web/src/styles.css` MUST
resolve through a CSS custom property declared in
`apps/web/src/styles/tokens.css` whose name begins with `--leading-`.
Magic numeric values (e.g. `line-height: 1.15;`) MUST NOT appear.

#### Scenario: every line-height uses a token
- **WHEN** any CSS rule under `apps/web/src/styles.css` declares
      `line-height`
- **THEN** its value MUST reference a token declared in `tokens.css`
      with a `--leading-*` name
- **AND** the implementation MUST be searchable as
      `line-height: var(--leading-...);`

#### Scenario: --leading-tight exists for the 1.15 step
- **WHEN** any consumer needs `line-height: 1.15`
- **THEN** `--leading-tight: 1.15;` MUST be declared in
      `tokens.css`
- **AND** consumers MUST use `var(--leading-tight)` rather than the
      literal value

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

