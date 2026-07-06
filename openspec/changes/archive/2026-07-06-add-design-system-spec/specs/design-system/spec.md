## ADDED Requirements

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
