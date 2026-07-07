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

### Requirement: Spacing uses an 8px-grid semantic ladder
The web frontend MUST expose a semantic spacing ladder as the
first-class way to express layout gaps, and the ladder MUST
resolve to multiples of 8 (8 / 16 / 24 / 32 / 48 / 64 / 96 px).
The ladder is declared in `apps/web/src/styles/tokens.css` as the
following aliases:

- `--space-xs` resolves to `8px`
- `--space-sm` resolves to `16px`
- `--space-md` resolves to `24px`
- `--space-lg` resolves to `32px`
- `--space-xl` resolves to `48px`
- `--space-2xl` resolves to `64px`
- `--space-3xl` resolves to `96px`

Each `--space-*` alias MUST be implemented as
`var(--spacing-N)` onto an existing 8px-grid primitive
(`--spacing-8 / --spacing-16 / --spacing-24 / --spacing-32 /
--spacing-48 / --spacing-64 / --spacing-96`).

The `--spacing-N` primitives remain available for fine-grained
borders, padding-edge nudges, and any value that does not
fit the 8px-grid ladder. New layout-gap code SHOULD prefer
`--space-*`.

#### Scenario: --space-* ladder is declared in tokens.css
- **WHEN** a developer inspects `apps/web/src/styles/tokens.css`
- **THEN** the `:root` block MUST declare `--space-xs`,
      `--space-sm`, `--space-md`, `--space-lg`, `--space-xl`,
      `--space-2xl`, `--space-3xl`
- **AND** each MUST resolve (transitively) to one of
      `8px`, `16px`, `24px`, `32px`, `48px`, `64px`, `96px`

#### Scenario: layout gaps use --space-* rather than ad-hoc spacing-N
- **WHEN** any CSS rule under `apps/web/src/styles.css` sets
      a layout-gap property (`gap`, `margin`, or `padding`) on a
      top-level page section, panel, or list
- **THEN** the value SHOULD resolve through `var(--space-*)`
- **AND** the literal value MUST NOT exceed `96px` (the top
      rung of the ladder) without an explicit override

#### Scenario: pre-existing dead --spacing-28 / --spacing-140 are pruned
- **WHEN** `tokens.css` is searched for the declared
      `--spacing-28` and `--spacing-140` primitives
- **THEN** neither token MUST be declared
- **AND** both `--spacing-28` and `--spacing-140` MUST be absent
      from every CSS file under `apps/web/src/` (verified by
      `grep -RE "var\(--spacing-(28|140)\)" apps/web/src/`
      returning no matches before deletion)
- **AND** every other declared `--spacing-N` primitive that is
      NOT one of the seven backing primitives
      (`--spacing-8 / 16 / 24 / 32 / 48 / 64 / 96`) MAY remain
      declared even if it currently has zero `var(...)`
      consumers; pruning those pre-existing dead primitives is
      out of scope for this change

### Requirement: Type scale is complete and body renders at 16 / 1.5
The web frontend MUST expose a complete type scale that
includes every named size a consumer is expected to need:
`12 / 13 / 14 / 16 / 17 / 20 / 24 / 32 / 48 / 64 / 72` px.

`--text-body` MUST resolve to `16px` and `--leading-body` MUST
resolve to `1.5`.

Each size MUST have a paired `--leading-*` token. Sizes `14`,
`16`, `17` MUST use `--leading-*: 1.5;` unless an existing
scenario in this capability pins them otherwise.

#### Scenario: every named size is declared in tokens.css
- **WHEN** `apps/web/src/styles/tokens.css` is searched for
      the type-scale tokens
- **THEN** every named size in the scale
      (`12 / 13 / 14 / 16 / 17 / 20 / 24 / 32 / 48 / 64 / 72` px)
      MUST be reachable as a CSS custom property under the
      `:root` block
- **AND** each size MUST be paired with a `--leading-*`
      token resolving to a unitless line-height
- **AND** the reachability MAY be via a numeric alias
      (`--text-14`, `--text-16`, `--text-17`) or via a
      semantic name (`--text-label` for 12,
      `--text-caption` for 13, `--text-body-lg` for 20,
      `--text-subheading` for 24, `--text-heading-sm` for 32,
      `--text-heading` for 48, `--text-heading-lg` for 64,
      `--text-display` for 72); both forms count
- **AND** the scale is exhaustive: no named size in
      `12 / 13 / 14 / 16 / 17 / 20 / 24 / 32 / 48 / 64 / 72`
      is missing a token

#### Scenario: --text-body and --leading-body resolve to 16 / 1.5
- **WHEN** `tokens.css` declares `--text-body` and
      `--leading-body`
- **THEN** `--text-body` MUST resolve to `16px`
- **AND** `--leading-body` MUST resolve to `1.5`
- **AND** every existing `var(--text-body)` /
      `var(--leading-body)` call site under `apps/web/src/`
      MUST keep resolving to those values without code change
      (the consumers automatically pick up the new values)

#### Scenario: unused --text-body-sm / --text-body-lg aliases do not regress
- **WHEN** `tokens.css` is searched for `--text-body-sm`,
      `--leading-body-sm`, `--tracking-body-sm`,
      `--text-body-lg`, `--leading-body-lg`,
      `--tracking-body-lg`
- **THEN** none of these tokens is referenced anywhere under
      `apps/web/src/` by `var(--...)` (verified by grep)
- **AND** the tokens MAY either remain declared or be pruned;
      either choice MUST NOT change any rendered font size

### Requirement: Inter Variable OpenType features are active for default text
The web frontend MUST activate Inter Variable's
single-storey `a` (`cv01`), curved `f` (`ss03`), slashed zero
(`zero`), and contextual alternates (`calt`) for all default
text. The activation MUST be a single rule on the `body`
selector that reads from a token declared in
`apps/web/src/styles/tokens.css`.

The token MUST be named `--font-feature-settings-default`
and MUST resolve to the string `"cv01", "ss03", "zero", "calt"`
(in that order).

#### Scenario: --font-feature-settings-default is declared
- **WHEN** `apps/web/src/styles/tokens.css` is inspected
- **THEN** the `:root` block MUST declare
      `--font-feature-settings-default`
- **AND** its value MUST equal the literal string
      `"cv01", "ss03", "zero", "calt"`

#### Scenario: body activates the default features
- **WHEN** `apps/web/src/styles.css` is searched for the
      `body` selector
- **THEN** it MUST contain a
      `font-feature-settings: var(--font-feature-settings-default);`
      declaration
- **AND** no other rule under `apps/web/src/styles.css`
      SHOULD override `font-feature-settings` for default
      text elements (`p`, `span`, `li`, `dt`, `dd`, `td`,
      `th`) without an explicit design rationale

#### Scenario: text uses single-storey a, curved f, slashed zero
- **WHEN** a user opens any page rendered by the web frontend
- **THEN** lowercase `a` glyphs in body text MUST render as
      Inter Variable's single-storey `a` (`cv01`)
- **AND** lowercase `f` glyphs MUST render as the curved `f`
      (`ss03`)
- **AND** the digit `0` MUST render as a slashed zero
      (`zero`), distinguishable from the letter `O` at typical
      body sizes

### Requirement: Card primitives are available as `--card-*` tokens
The web frontend MUST expose a `--card-*` token family so
that card surfaces share a single source of truth for their
background, border, padding, radius, shadow, and internal
gap. All `--card-*` tokens MUST be declared in
`apps/web/src/styles/tokens.css` and MUST resolve to existing
primitives or fixed color values declared in the same file.

The family is:

- `--card-bg`            resolves to `var(--surface-obsidian)`
- `--card-border-color`  resolves to `rgba(255, 255, 255, 0.06)`
- `--card-padding-x`     resolves to `var(--spacing-24)`
- `--card-padding-y`     resolves to `var(--spacing-20)`
- `--card-radius`        resolves to `var(--radius-cards)`
- `--card-shadow`        resolves to `var(--shadow-subtle-3)`
- `--card-gap`           resolves to `var(--element-gap)`

#### Scenario: --card-* tokens are declared in tokens.css
- **WHEN** `apps/web/src/styles/tokens.css` is inspected
- **THEN** the `:root` block MUST declare every token in
      the list above
- **AND** each token's value MUST match its documented
      resolution

#### Scenario: --card-* tokens do not duplicate declarations
- **WHEN** any CSS file under `apps/web/src/` (other than
      `tokens.css`) declares a CSS custom property whose name
      starts with `--card-`
- **THEN** that declaration is non-conforming with this
      capability (consumers must read from `tokens.css`)

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

