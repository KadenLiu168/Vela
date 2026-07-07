## MODIFIED Requirements

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

## ADDED Requirements

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

### Requirement: Display font family token is registered

The web frontend MUST declare `--font-display` in
`apps/web/src/styles/tokens.css` and load a corresponding
`@font-face` rule in `apps/web/src/styles.css`. The token value
MUST chain an open-source display mono family first and MUST be
named with intent (not with the OFL substitute), mirroring the
convention applied to `--font-berkeley-mono`.

(Same-change migration: original proposal cited "Departure Mono"
as the design-intent primary; this change ships IBM Plex Mono
(OFL) as the served woff2 and treats "Söhne Mono" as the design
intent in the token name chain.)

#### Scenario: --font-display is declared and chained correctly
- **WHEN** `apps/web/src/styles/tokens.css` is inspected
- **THEN** the `:root` block MUST declare `--font-display`
- **AND** the value MUST chain `"IBM Plex Mono"` first
- **AND** the value MUST chain `"Söhne Mono"` as the design-intent
      fallback
- **AND** the remainder of the chain MUST list the standard
      monospace fallbacks (`ui-monospace, SFMono-Regular, Menlo,
      Monaco, Consolas, monospace`) in that exact order

#### Scenario: @font-face and preload pair with --font-display
- **WHEN** `apps/web/src/styles.css` is searched for
      `@font-face`
- **THEN** at least one rule MUST declare `font-family:
      "IBM Plex Mono"` and reference a woff2 file under
      `apps/web/public/fonts/`
- **AND** the same woff2 MUST be preloaded by
      `apps/web/index.html` via
      `<link rel="preload" as="font" type="font/woff2" crossorigin>`
- **AND** no commercial-only font may be added to
      `apps/web/public/fonts/` (license headers or whitelisted
      OFL / SIL / MIT / Apache-2.0 only)

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
