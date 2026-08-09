# design-system Specification

## Purpose
Defines the canonical web design-token system: every CSS custom property lives in `apps/web/src/styles/tokens.css` as a single `:root` block, wired via `@import` and referenced through `var(--*)`.
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
(Berkeley Mono in the Linear reference system), not after the current
runtime implementation.

#### Scenario: token name is --font-berkeley-mono
- **WHEN** `tokens.css` declares the monospace family token
- **THEN** the token name MUST be `--font-berkeley-mono`
- **AND** the value MUST chain
      `"Inter Variable", "Berkeley Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`
      in that exact order
- **AND** the value's first entry (`"Inter Variable"`) MUST match
      the `font-family` declared by the `@font-face` rule for the
      Inter Variable woff2 in `apps/web/src/styles.css`

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

### Requirement: Secondary buttons render a selected state when pressed
A `button-secondary` button that carries `aria-pressed="true"` MUST render as selected with the inverted fill (`background: var(--color-mist)`, `color: var(--color-void)`, `border: 1px solid var(--color-mist)`). Single-select filter controls (e.g., the Signals SOURCE filter) are part of the three-variant button contract: every such `<button>` MUST carry exactly one variant className, and its visual treatment MUST come from the variant class rather than from a bespoke segmented style.

#### Scenario: pressed secondary button uses the inverted fill
- **WHEN** a `button-secondary` element has `aria-pressed="true"`
- **THEN** its `background` MUST be `var(--color-mist)`
- **AND** its `color` MUST be `var(--color-void)`
- **AND** its `border` MUST be `1px solid var(--color-mist)`

#### Scenario: selection controls declare a variant className
- **WHEN** a single-select filter control (e.g., the Signals SOURCE filter) renders its options as `<button>` elements
- **THEN** every such button MUST include exactly one of `button-primary`, `button-secondary`, or `button-tertiary` in its className
- **AND** its visual treatment MUST come from the declared variant class, not from a bespoke segmented style
- **AND** the selected option MUST be communicated via `aria-pressed="true"` and the inverted fill of the variant class

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

In addition to the body-sized ladder above, the web frontend MUST
expose a card-type-scale ladder with four rungs (`meta`, `body`,
`emphasis`, `display`) bound to specific visual roles. The card
ladder is the canonical source for any typography that renders
inside or on a card surface. Both ladders MUST be declared in
`apps/web/src/styles/tokens.css` and MUST NOT duplicate values
across rungs (one rung, one source).

The card-type-scale ladder is:

- `--card-meta-size: 11px;` paired with `--leading-meta: 1.4;`
- `--card-body-size: 14px;` paired with `--leading-body-card: 1.5;`
- `--card-emphasis-size: 28px;` paired with `--leading-emphasis: 1.3;`
- `--card-display-size: 40px;` paired with `--leading-display-card: 1.15;`

#### Scenario: every named size is declared in tokens.css
- **WHEN** `apps/web/src/styles/tokens.css` is searched for the
      type-scale tokens
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
      `apps/web/src/` by `var(...)` (verified by grep)
- **AND** the tokens MAY either remain declared or be pruned;
      either choice MUST NOT change any rendered font size

#### Scenario: card-type-scale ladder is declared in tokens.css
- **WHEN** `apps/web/src/styles/tokens.css` is inspected
- **THEN** the `:root` block MUST declare every token of the
      card-type-scale ladder listed in the requirement body
      (eight tokens: four `<role>-size` and four `<role>-leading`)
- **AND** each declared value MUST match the resolution pinned
      in this requirement

#### Scenario: card-type-scale rungs map onto card visual roles
- **WHEN** `apps/web/src/styles.css` is searched for any rule
      inside a card surface (`.dashboard-panel`,
      `.panel-primary`, `.metric`, `.compact-list`,
      `.status-pill`, `.etf-row`, `.fetch-log-entry`,
      `.backtest-run-form`, `.operation-summary`)
- **THEN** the rule's `font-size` MUST resolve through one of
      the four ladder rungs (`--card-meta-size` /
      `--card-body-size` / `--card-emphasis-size` /
      `--card-display-size`) rather than through a non-ladder
      `--text-*` token
- **AND** the corresponding `--leading-*` token from this
      capability MUST be applied to the same rule's
      `line-height`

### Requirement: Inter Variable webfont is a size-bounded reproducible subset

The web frontend MUST serve a reproducibly generated Latin-1-focused subset of
Inter Variable as its sole project-hosted webfont. The committed served WOFF2
MUST be no larger than 98,304 bytes, MUST retain the source `opsz` and `wght`
variable axes, and MUST remain upright for the declared CSS `300–700` range.

#### Scenario: subset stays within the font budget

- **WHEN** the committed Inter Variable subset under `apps/web/public/fonts/` is inspected
- **THEN** it MUST be a valid WOFF2 variable font
- **AND** its on-disk size MUST be at most 98,304 bytes
- **AND** its variable metadata MUST include `opsz` and `wght` axes matching
  the canonical source and MUST NOT include `ital` or `slnt`
- **AND** no full, static, italic, or additional project-hosted font file MUST coexist with it

#### Scenario: subset generation is reproducible

- **WHEN** a developer follows the repository's documented font-generation
  command using the pinned and locked WOFF2 toolchain, canonical source with
  verified SHA-256, and committed Unicode manifest
- **THEN** the command MUST produce the webfont consumed by the frontend
- **AND** two clean generations from the same inputs MUST be byte-identical
- **AND** a clean generation MUST be byte-identical to the committed served
  subset
- **AND** the canonical source MUST be stored outside
  `apps/web/public/fonts/` with the upstream OFL license
- **AND** the manifest MUST be the source of truth for both the font subset and its CSS `unicode-range`

### Requirement: Inter subset preserves Vela typography coverage

The Inter Variable subset MUST retain source-mapped glyphs for Basic Latin,
Latin-1, combining diacritics, the reviewed punctuation and currency set, and
the explicit UI symbols used by Vela. It MUST retain the `cv01`, `ss03`,
`zero`, and `calt` OpenType features plus `ccmp`, `kern`, `mark`, and `mkmk`,
and MUST allow characters outside its declared Unicode coverage to resolve
through the existing fallback chain.

#### Scenario: application text and symbols remain covered

- **WHEN** the subset cmap and layout tables are inspected
- **THEN** ordinary English letters, digits, punctuation, representative
  Latin-1 characters, and combining marks MUST be present
- **AND** `·` (`U+00B7`), `—` (`U+2014`), `…` (`U+2026`), `⌘` (`U+2318`), `✓` (`U+2713`), and `✗` (`U+2717`) MUST be present
- **AND** the `cv01`, `ss03`, `zero`, `calt`, `ccmp`, `kern`, `mark`, and
  `mkmk` features MUST be available for retained glyphs

#### Scenario: excluded scripts use system fallback

- **WHEN** an ETF name containing Chinese characters is rendered next to Latin characters
- **THEN** the Latin characters MUST render with Inter Variable
- **AND** the Chinese characters MUST remain legible through the existing `system-ui` fallback chain
- **AND** rendering the name MUST NOT trigger another project-hosted font request

#### Scenario: undeclared repertoires are excluded

- **WHEN** the subset cmap is inspected
- **THEN** representative Greek, Cyrillic, Latin Extended, IPA, and
  Vietnamese precomposed code points outside the manifest MUST NOT be present
- **AND** their absence MUST NOT change the Inter rendering of retained Latin characters

### Requirement: Only the Inter subset is preloaded

The frontend MUST preload the same Inter Variable subset referenced by its `@font-face` rule. The `@font-face` rule MUST declare the subset's reviewed `unicode-range` and MUST preserve `font-display: swap`, normal style, and the `300–700` weight range.

#### Scenario: preload and font-face target the same subset

- **WHEN** `apps/web/index.html` and `apps/web/src/styles.css` are inspected
- **THEN** exactly one font preload MUST exist
- **AND** its URL MUST equal the URL in the Inter Variable `@font-face` source
- **AND** that URL MUST identify the Latin subset rather than the removed full font

#### Scenario: production build contains only the subset

- **WHEN** the web production build completes
- **THEN** the referenced Inter Variable subset MUST exist under `apps/web/dist/fonts/`
- **AND** the former full Inter Variable resource MUST NOT exist in the build output
- **AND** the built page MUST load the subset without a font-related HTTP error

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

### Requirement: State component set is exported from the components barrel
The web frontend MUST expose the Empty / Loading / Skeleton /
Error state-UI primitives as a single named family that is
importable from `apps/web/src/components` (the canonical barrel
at `apps/web/src/components/index.ts`).

The family is:

- **`EmptyState`** — paragraph-shaped empty surface
  (`<p class="status-surface status-surface-empty empty-state">`)
  for "no data yet" or "nothing matches" states
- **`FeedbackMessage`** — banner-shaped status surface
  (`<div role="status" | "alert" class="status-surface
  feedback-message feedback-message-{variant}">`) for the
  `loading | success | error | info` variants
- **`Skeleton`** — placeholder primitive for content whose
  shape is known but whose data is still loading. Renders an
  element with the `.skeleton` class plus optional
  `.skeleton-pulse` animation
- **`ErrorBoundary`** — React class component that catches
  render-time exceptions in its `children` subtree and renders
  a `<FeedbackMessage variant="error">` fallback

All four components MUST be re-exported by
`apps/web/src/components/index.ts`. New code MUST import the
state components from this barrel rather than from the
underlying files.

#### Scenario: barrel exports the four state components
- **WHEN** a developer inspects `apps/web/src/components/index.ts`
- **THEN** the file MUST re-export `EmptyState`,
      `FeedbackMessage`, `Skeleton`, and `ErrorBoundary` as
      named exports
- **AND** any page or test under `apps/web/src/` that needs
      a state component MUST import from
      `"../components"` (or the equivalent relative path that
      resolves to the barrel) rather than from the underlying
      component files

#### Scenario: Skeleton pulse respects prefers-reduced-motion
- **WHEN** the OS reports `prefers-reduced-motion: reduce`
- **THEN** any `<Skeleton>` element with the `.skeleton-pulse`
      class MUST NOT animate (its `animation` property MUST
      resolve to `none` and its `opacity` MUST remain constant)
- **AND** the placeholder MUST still be visually present
      (the surface color and dimensions are preserved)

#### Scenario: ErrorBoundary renders a feedback-message-error fallback on child errors
- **WHEN** a child component passed to `<ErrorBoundary>`
      throws a render-time exception
- **THEN** the boundary MUST render a
      `<FeedbackMessage variant="error">` element (or the
      `fallback` prop if provided) in place of the failing
      subtree
- **AND** the rest of the AppShell (header, nav, main
      layout) MUST continue to render normally

#### Scenario: Skeleton default is inline span
- **WHEN** a `<Skeleton />` element is rendered without props
- **THEN** it MUST render as an inline `<span>` element
- **AND** its rendered width MUST default to `100%` of its
      containing inline context
- **AND** its rendered height MUST default to `0.75em` (one
      line of body text)

### Requirement: Design system invariants are enforced by Stylelint
The web frontend MUST enforce the design-system invariants
already shipped in earlier changes via Stylelint. The Stylelint
config lives at `apps/web/.stylelintrc.json` and is invoked by
the `npm --prefix apps/web run lint:css` script.

The config MUST enforce, at minimum, these five rule
categories:

1. **No descendant-selector button styling.** Selectors of the
   form `.operation-list button` or any other ancestry-based
   button selector MUST be flagged.
2. **No literal numeric line-heights.** A `line-height`
   declaration whose value is a plain number or `<number><unit>`
   (e.g. `1.4`, `1.15`, `140ms`) MUST be flagged; only
   `var(...)`, `inherit`, `initial`, `unset`, `revert` are
   allowed.
3. **No literal `border-radius` pixel values.** A
   `border-radius` declaration whose value is a plain pixel
   literal (e.g. `4px`, `12px`) MUST be flagged; only `var(...)`
   and the keyword values (`inherit`, `initial`, etc.) are
   allowed.
4. **No `:root` declarations outside `tokens.css`.** A `:root`
   selector MUST NOT appear in any CSS file under
   `apps/web/src/` other than `apps/web/src/styles/tokens.css`.
5. **Acid-lime as fill is reserved.** A `background-color:
   var(--color-acid-lime)` or `outline-color:
   var(--color-acid-lime)` declaration MUST NOT appear under
   `apps/web/src/styles.css`. The CTA fill (`.button-primary`'s
   `background: var(--color-acid-lime)`) is the one place the
   fill appears and is enforced by code review (the value
   keyword differs from `background-color`). Other non-fill uses
   (focus rings via `border-color`, underlines via `box-shadow:
   inset`, text decoration via `text-decoration-color`, SVG
   `stroke` / `fill`) are intentionally allowlisted at code
   review time.

A Stylelint violation is a CI failure for rules 1–4.
Rule 5 is a lint-level rule (catches the most common misuse
patterns) plus code review (covers the allowlist).

#### Scenario: lint:css script exists and runs
- **WHEN** a developer runs `npm --prefix apps/web run lint:css`
- **THEN** the command MUST exit 0 if no design-system
      invariants are violated
- **AND** the command MUST exit non-zero with a per-file
      violation report if any rule above is violated
- **AND** the script MUST be wired into the project's CI
      pipeline (a future change may move the wiring; this
      change lands the script and config)

#### Scenario: descendant-selector button styling is flagged
- **WHEN** any CSS rule under `apps/web/src/styles.css` (or
      any future CSS file) selects a button by ancestry alone
      (e.g. `.operation-list button { ... }`)
- **THEN** `npm --prefix apps/web run lint:css` MUST exit
      non-zero and report the offending file:line

#### Scenario: literal line-height is flagged
- **WHEN** any CSS rule declares `line-height: <number>` (e.g.
      `line-height: 1.4`)
- **THEN** the lint script MUST flag it and direct the
      contributor to use a `--leading-*` token instead

#### Scenario: literal border-radius is flagged
- **WHEN** any CSS rule declares `border-radius: <number>px`
      (e.g. `border-radius: 4px`)
- **THEN** the lint script MUST flag it and direct the
      contributor to use a `--radius-*` token instead

#### Scenario: acid-lime fill misuse is flagged
- **WHEN** any CSS rule declares `background-color:
      var(--color-acid-lime)` or `outline-color:
      var(--color-acid-lime)`
- **THEN** the lint script MUST flag it and direct the
      contributor to either use `--feedback-accent-*` (for
      non-CTA accents) or restructure as `.button-primary`
      (for the per-view primary CTA). The lone legitimate
      `background: var(--color-acid-lime)` on `.button-primary`
      is the per-view primary CTA fill and is enforced by code
      review, not by this lint rule

### Requirement: Component catalog is reachable via Ladle
The web frontend MUST expose a dev-only component catalog that
renders each state component with controls for its variant /
shape / width / height props. The catalog is implemented with
`@ladle/react`, configured at `apps/web/.ladle/config.mjs`,
and started via the `npm --prefix apps/web run ladle` script.

A story MUST exist for each state component in
`apps/web/src/components/`:

- `FeedbackMessage.stories.tsx` — one story per variant
  (`loading | success | error | info`) plus a default
- `Skeleton.stories.tsx` — text default, block shape, circle
  variant with diameter variations
- `ErrorBoundary.stories.tsx` — happy path, default fallback,
  custom fallback prop
- `EmptyState.stories.tsx` — empty state with default content,
  and one paired with `EmptyAction`

The catalog is dev-only and MUST NOT contribute to the
production bundle.

#### Scenario: ladle script exists and starts the dev catalog
- **WHEN** a developer runs `npm --prefix apps/web run ladle`
- **THEN** a local dev server MUST start on
      `http://localhost:61000` (or a documented alternative
      port)
- **AND** the catalog MUST list a story for each of the four
      state components
- **AND** each story MUST render the component with its
      documented props wired to Ladle controls

#### Scenario: stories use the production components directly
- **WHEN** any `.stories.tsx` file under
      `apps/web/src/components/` renders a component
- **THEN** the rendered element MUST be the actual production
      component (imported from the same module the app uses),
      not a re-implementation or a mock
- **AND** the production build (`npm --prefix apps/web run
      build`) MUST NOT include any `.stories.tsx` file in the
      bundle (Vite / Ladle handle this separation)

### Requirement: Token reference doc is generated from tokens.css
The web frontend MUST ship a Markdown token reference generated
from `apps/web/src/styles/tokens.css`. The generator is at
`scripts/build-tokens-reference.mjs`, has zero runtime
dependencies (uses Node built-ins only), and is invoked by
`npm --prefix apps/web run build:tokens-doc`.

The generated output is `docs/tokens.md`. It MUST list every
token declared in the `:root { ... }` block, grouped by the
section comments already present in `tokens.css` (Colors,
Surfaces, Typography families, etc.). For each token it MUST
show the token name and its resolved value (chasing
`var(...)` aliases to a final pixel / color / numeric value).

The generated file is committed to git; subsequent edits to
`tokens.css` require re-running the generator and committing
the regenerated output.

#### Scenario: tokens.md is generated and committed
- **WHEN** a developer runs
      `npm --prefix apps/web run build:tokens-doc`
- **THEN** the file `docs/tokens.md` MUST exist and MUST
      contain one Markdown section per token group declared
      in `apps/web/src/styles/tokens.css`
- **AND** the file MUST be committed to the repository
      (verifiable via `git ls-files docs/tokens.md`)

#### Scenario: token aliases resolve to concrete values
- **WHEN** the generator encounters a token whose value is
      `var(--other-token)`
- **THEN** the Markdown output MUST show both the alias and
      the chained resolved value (e.g.
      `--space-xs: var(--spacing-8) → 8px`)

#### Scenario: generator has zero runtime dependencies
- **WHEN** `scripts/build-tokens-reference.mjs` is inspected
- **THEN** the script MUST NOT `import` or `require` any
      module other than Node built-ins
- **AND** the script MUST be invokable on a fresh `node`
      install with no `npm install` step

### Requirement: Card typography tracking tokens are declared

The web frontend MUST declare two tracking (letter-spacing) tokens
in `apps/web/src/styles/tokens.css` whose purpose is to distinguish
the meta rung from body text and to tighten numeric emphasis:

- `--tracking-meta` resolves to `0.06em`
- `--tracking-numeral` resolves to `-0.01em`

These tokens are part of the card-type-scale family and MUST be
applied per the ladder-to-role mapping in the `card-type-scale`
capability.

#### Scenario: tracking tokens are declared in tokens.css
- **WHEN** `apps/web/src/styles/tokens.css` is searched for
      `tracking-meta` and `tracking-numeral`
- **THEN** both tokens MUST be declared under the `:root` block
- **AND** `--tracking-meta` MUST equal `0.06em`
- **AND** `--tracking-numeral` MUST equal `-0.01em`

#### Scenario: tracking tokens have no duplicate declarations
- **WHEN** any CSS file under `apps/web/src/` (other than
      `tokens.css`) declares a CSS custom property named
      `--tracking-meta` or `--tracking-numeral`
- **THEN** that declaration is non-conforming with this
      capability


### Requirement: Card container padding routes through --card-padding-y

`apps/web/src/styles.css` rules that style `.dashboard-panel` (or the same class scoped to `.dashboard-page` / `.detail-page`) MUST source their `padding` (when the value is one of the canonical card paddings) through `var(--card-padding-y)` / `var(--card-padding-x)` rather than through bare `var(--spacing-N)` primitives.

#### Scenario: dashboard-panel padding uses card padding tokens
- **WHEN** `apps/web/src/styles.css` is searched for the rules
      targeting `.dashboard-panel`, `.dashboard-page
      .dashboard-panel`, and `.detail-page .dashboard-panel`
- **THEN** each rule's `padding` MUST resolve through
      `var(--card-padding-y)` (or `--card-padding-x` for the
      horizontal axis)
- **AND** no rule under these selectors MAY use a bare
      `var(--spacing-N)` for card padding

### Requirement: Display font token resolves to Inter Variable

The `--font-display` editorial display font token MUST resolve
to Inter Variable at runtime. Hierarchy (heading vs data vs body)
is created through font weight and size, not through font family
switching.

#### Scenario: --font-display uses Inter Variable
- **WHEN** `tokens.css` declares the editorial display font token
- **THEN** the token name MUST be `--font-display`
- **AND** the value MUST chain
      `"Inter Variable", "Söhne Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`
      in that exact order
- **AND** the first effective font family at runtime MUST be
      `"Inter Variable"` (loaded via the Inter Variable @font-face rule)

#### Scenario: --font-display and --font-berkeley-mono use the same font
- **WHEN** any element references `--font-display` or `--font-berkeley-mono`
- **THEN** both tokens MUST resolve to the same active font family
      at runtime (`"Inter Variable"`)
- **AND** visual hierarchy MUST be achieved through `font-weight`,
      `font-size`, and `letter-spacing` alone

### Requirement: No IBM Plex Mono font resources

The web frontend MUST NOT load or reference the IBM Plex Mono font
family. All @font-face rules and woff2 files for IBM Plex Mono
SHALL be removed.

#### Scenario: no IBM Plex Mono @font-face is declared
- **WHEN** `apps/web/src/styles.css` is inspected
- **THEN** it MUST NOT contain an `@font-face` rule for
      `font-family: "IBM Plex Mono"`
- **AND** no IBM Plex Mono woff2 files exist under
      `apps/web/public/fonts/`

#### Scenario: no IBM Plex Mono preload
- **WHEN** `apps/web/index.html` is inspected
- **THEN** it MUST NOT contain a `<link rel="preload">` element
      referencing any IBM Plex Mono woff2 file

### Requirement: Inter Variable is the sole loaded font

The web frontend MUST load exactly one font family at build time:
Inter Variable (300–700 variable weight, woff2 format).
Token aliases (`--font-display`, `--font-berkeley-mono`) MAY
reference the same font family with different fallback chains.

#### Scenario: only Inter Variable @font-face is declared
- **WHEN** `apps/web/src/styles.css` is inspected
- **THEN** the only `@font-face` rule present MUST be for
      `font-family: "Inter Variable"`
- **AND** the only font files under `apps/web/public/fonts/` MUST
      be the Inter Variable woff2

### Requirement: Low-contrast palette colors are not readable text colors
The web frontend MUST NOT use `--color-ash` or `--color-smoke` as the sole `color` value for readable text rendered on dark app surfaces. Readable text includes headings, body copy, labels, table text, command-palette text, status-pill text, placeholders, and other text whose characters convey information to sighted users.

Readable secondary or metadata text on dark surfaces MUST use at least `--color-fog`; more important text MUST use a higher-contrast token such as `--color-mist` or `--color-paper`.

`--color-ash` and `--color-smoke` MAY remain in use for decorative or structural roles, including borders, dividers, SVG grid lines, subdued accents, and visual separators that are not the sole carrier of information.

#### Scenario: readable text avoids ash and smoke
- **WHEN** a CSS rule under `apps/web/src/` sets the foreground `color` for readable text on a dark app surface
- **THEN** the value MUST NOT be `var(--color-ash)` or `var(--color-smoke)`
- **AND** the value MUST resolve to `var(--color-fog)`, `var(--color-mist)`, `var(--color-paper)`, or a higher-contrast semantic/status token appropriate to the state

#### Scenario: command palette metadata remains readable
- **WHEN** the command palette renders placeholder text or row-kind metadata
- **THEN** those text roles MUST use a color token that meets WCAG AA normal-text contrast on the palette surface
- **AND** they MUST NOT use `var(--color-ash)` or `var(--color-smoke)` as their foreground text color

#### Scenario: neutral status text remains readable
- **WHEN** a neutral or fallback status pill renders text such as an empty or no-data state
- **THEN** the text color MUST meet WCAG AA normal-text contrast on the pill's rendered surface
- **AND** an empty-state accent token that resolves to `var(--color-smoke)` MUST NOT be used as the sole text color

#### Scenario: decorative uses may stay subdued
- **WHEN** a CSS rule uses `var(--color-ash)` or `var(--color-smoke)` for non-text decoration such as `border-color`, SVG `stroke`, chart grid lines, or a purely visual separator
- **THEN** that use remains conforming
- **AND** if the separator is rendered as a text character in the DOM, it MUST be hidden from assistive technology when it does not convey information

