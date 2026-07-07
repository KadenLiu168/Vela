## ADDED Requirements

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
