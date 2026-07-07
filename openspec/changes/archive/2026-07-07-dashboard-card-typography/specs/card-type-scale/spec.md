## ADDED Requirements

### Requirement: Card typography ladder is exposed as four semantic rungs

The web frontend MUST expose a `card-type-scale` ladder in
`apps/web/src/styles/tokens.css` with exactly four rungs (`meta`,
`body`, `emphasis`, `display`). Each rung MUST be a pair of CSS
custom properties: a `<role>-size` token and a `<role>-leading`
token. The values MUST be:

- `--card-meta-size` resolves to `11px`; `--leading-meta` resolves to `1.4`
- `--card-body-size` resolves to `14px`; `--leading-body-card` resolves to `1.5`
- `--card-emphasis-size` resolves to `28px`; `--leading-emphasis` resolves to `1.3`
- `--card-display-size` resolves to `40px`; `--leading-display-card` resolves to `1.15`

The ladder MUST be reachable from `apps/web/src/styles.css` through
`var(--card-*)` references without redeclaration.

#### Scenario: every ladder token is declared in tokens.css
- **WHEN** `apps/web/src/styles/tokens.css` is inspected
- **THEN** the `:root` block MUST declare
      `--card-meta-size`, `--leading-meta`, `--card-body-size`,
      `--leading-body-card`, `--card-emphasis-size`,
      `--leading-emphasis`, `--card-display-size`, and
      `--leading-display-card`
- **AND** each declared value MUST equal the resolution in this
      requirement (verified by reading the source declaration or by
      `scripts/build-tokens-reference.mjs`)

#### Scenario: every card type rung is consumed by at least one rule
- **WHEN** `apps/web/src/styles.css` is searched for
      `var(--card-meta-size)`, `var(--card-body-size)`,
      `var(--card-emphasis-size)`, `var(--card-display-size)`
- **THEN** each token MUST appear in at least one CSS rule
- **AND** no token from the ladder MAY be declared without any
      consumer (i.e. dead-on-arrival tokens are non-conforming)

### Requirement: Tracking tokens for meta labels and numeric emphasis

The web frontend MUST declare two tracking (letter-spacing) tokens
in `apps/web/src/styles/tokens.css`:

- `--tracking-meta` resolves to `0.06em`
- `--tracking-numeral` resolves to `-0.01em`

`--tracking-meta` MUST be applied to any element that renders the
meta ladder rung as label text (eyebrow / status pill / form label
/ `compact-list` dt / `metric` label). `--tracking-numeral` MUST
be applied together with `font-variant-numeric: tabular-nums` to
any element that renders emphasis-or-larger numeric content
(`panel-primary`, `metric` strong, `etf-row-symbol`,
`fetch-log-entry__time`).

#### Scenario: tracking-meta is declared and applied to meta labels
- **WHEN** `apps/web/src/styles.css` is searched for any rule
      that consumes `var(--card-meta-size)`
- **THEN** the same rule MUST declare
      `letter-spacing: var(--tracking-meta)`
- **AND** the rule MUST also declare `text-transform: uppercase`

#### Scenario: tabular-nums pairs with tracking-numeral
- **WHEN** `apps/web/src/styles.css` is searched for any rule
      that consumes `var(--card-emphasis-size)` or
      `var(--card-display-size)`
- **THEN** the same rule MUST declare
      `font-variant-numeric: tabular-nums`
- **AND** the rule MUST declare
      `letter-spacing: var(--tracking-numeral)`

### Requirement: Display font family is exposed for card titles

The web frontend MUST declare `--font-display` in
`apps/web/src/styles/tokens.css` and load a corresponding
`@font-face` rule in `apps/web/src/styles.css`. The token value
MUST chain an open-source display mono family first, followed by
fallbacks in this exact order:

```
--font-display: "IBM Plex Mono", "Söhne Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
```

(Same-change migration: the original proposal cited "Departure
Mono" as the design-intent primary; this change adopts IBM Plex
Mono (OFL) as the served woff2 and treats "Söhne Mono" as the
design intent in the token name chain.)

`@font-face` MUST point at a woff2 hosted under
`apps/web/public/fonts/`. The woff2 file MUST be OFL, SIL, MIT, or
Apache-2.0 licensed (no commercial-only font may be added).

`--font-display` MUST be applied to `panel-heading h3` (card
title) and `page-heading h1` (page title). It MUST NOT be applied
to any text element below subheading size (`compact-list` dt / dd,
`metric` label / value, `panel-primary`, button text).

#### Scenario: --font-display token and @font-face are paired
- **WHEN** `apps/web/src/styles/tokens.css` is inspected
- **THEN** the `:root` block MUST declare `--font-display` with
      the chained value above (IBM Plex Mono first)
- **AND** `apps/web/src/styles.css` MUST contain at least one
      `@font-face` rule whose `font-family` is the first chained
      value (`"IBM Plex Mono"`)
- **AND** the `src` of that `@font-face` MUST reference a woff2
      file under `apps/web/public/fonts/` (Regular / Medium /
      SemiBold weight variants are all allowed and SHOULD all be
      declared)
- **AND** `apps/web/index.html` MUST preload the Regular (and
      optional Medium) woff2 via
      `<link rel="preload" as="font" type="font/woff2" crossorigin>`

#### Scenario: display font applies only to titles
- **WHEN** `apps/web/src/styles.css` is searched for any rule
      declaring `font-family: var(--font-display)`
- **THEN** the rule's selector MUST match either
      `.panel-heading h3` or `.page-heading h1` (and documented
      descendants of those)
- **AND** no rule MUST apply `var(--font-display)` to elements
      tagged with `compact-list`, `metric`, `panel-primary`, or
      `button-*` class selectors

### Requirement: Every card visual role maps to exactly one ladder rung

Each visual role used by the web frontend in or on a card surface MUST map to exactly one rung of the card-type-scale ladder, with the mapping documented in the table below.

| Role | Selector(s) | Rung | Weight |
|---|---|---|---|
| Meta label | `.panel-heading span`, `.status-pill`, `.compact-list dt`, `.metric span`, `.backtest-run-form label > span` | meta | 590 (semibold) |
| Body value | `.compact-list dd`, `.metric strong` (only when the metric is not the numeric headline), `.operation-summary strong`, `.operation-link strong`, `.backtest-run-form input`, `.fetch-log-entry__meta`, `.fetch-log-entry__error p`, `.etf-row-symbol`, `.etf-row-name`, `.etf-row-dot` | body | 510 (medium) for value text, 400 (regular) for input text |
| Emphasis (card primary value) | `.panel-primary`, `.metric strong` | emphasis | 510 (medium) |
| Display (detail-page numeric headline) | `.detail-page .metric-card dd` | display | 510 (medium) |

The mapping is total: every visual role above MUST consume its
rung's size / leading / tracking tokens. No role may consume a
non-ladder size (e.g. `var(--text-caption)` for body content;
legacy `var(--text-caption)` may still back the meta label during
migration but consumers SHOULD migrate to the card-type-scale).

#### Scenario: meta label role uses meta rung
- **WHEN** `apps/web/src/styles.css` is searched for rules
      targeting `.panel-heading span`, `.status-pill`,
      `.compact-list dt`, `.metric span`, or
      `.backtest-run-form label > span`
- **THEN** the rule MUST reference `var(--card-meta-size)` for
      font-size
- **AND** the rule MUST reference `var(--leading-meta)` for
      line-height
- **AND** the rule MUST declare `font-weight: var(--font-weight-semibold)`
      (or the literal `590`)

#### Scenario: body value role uses body rung
- **WHEN** `apps/web/src/styles.css` is searched for rules
      targeting `.compact-list dd`, `.operation-summary strong`,
      `.operation-link strong`, `.backtest-run-form input`,
      `.fetch-log-entry__meta`, `.fetch-log-entry__error p`,
      `.etf-row-symbol`, `.etf-row-name`, or `.etf-row-dot`
- **THEN** the rule MUST reference `var(--card-body-size)` for
      font-size
- **AND** the rule MUST reference `var(--leading-body-card)` for
      line-height

#### Scenario: emphasis role uses emphasis rung with tabular-nums
- **WHEN** `apps/web/src/styles.css` is searched for rules
      targeting `.panel-primary` (within `.dashboard-page` or
      `.detail-page`) or `.metric strong`
- **THEN** the rule MUST reference `var(--card-emphasis-size)`
      for font-size
- **AND** the rule MUST reference `var(--leading-emphasis)` for
      line-height
- **AND** the rule MUST declare
      `font-variant-numeric: tabular-nums`

#### Scenario: display role uses display rung with display font
- **WHEN** `apps/web/src/styles.css` is searched for the rule
      targeting `.detail-page .metric-card dd`
- **THEN** the rule MUST reference `var(--card-display-size)`
      for font-size
- **AND** the rule MUST reference `var(--leading-display-card)`
      for line-height
- **AND** the rule MUST declare
      `font-family: var(--font-berkeley-mono)` (mono on detail
      headlines preserves numerical comparison)

### Requirement: Dashboard and Detail pages render compact-list identically

Both Dashboard page (`.dashboard-page`) and Detail pages (Signal Detail + Backtest Detail, scoped under `.detail-page`) MUST render `.compact-list` (dt / dd) with identical font-family, font-size, line-height, letter-spacing, and text-transform.

#### Scenario: dashboard and detail compact-list dt are identical
- **WHEN** the Dashboard page renders its `.compact-list`
- **THEN** each `dt`'s font-family MUST resolve to
      `var(--font-inter-variable)`
- **AND** its font-size MUST resolve to `var(--card-meta-size)`
- **AND** its line-height MUST resolve to `var(--leading-meta)`
- **AND** its letter-spacing MUST resolve to
      `var(--tracking-meta)`
- **AND** its text-transform MUST be `uppercase`
- **AND** the same visual outcome MUST occur on the Detail pages

#### Scenario: dashboard and detail compact-list dd are identical
- **WHEN** the Dashboard page renders its `.compact-list`
- **THEN** each `dd`'s font-family MUST resolve to
      `var(--font-inter-variable)`
- **AND** its font-size MUST resolve to `var(--card-body-size)`
- **AND** its line-height MUST resolve to
      `var(--leading-body-card)`
- **AND** its font-weight MUST resolve to
      `var(--font-weight-medium)` (510)
- **AND** the same visual outcome MUST occur on the Detail pages

#### Scenario: dashboard and detail panel-primary are identical
- **WHEN** the Dashboard page renders a `.panel-primary` element
      (e.g. strategy_id, signal number, backtest number)
- **THEN** its font-size MUST resolve to
      `var(--card-emphasis-size)`
- **AND** its line-height MUST resolve to
      `var(--leading-emphasis)`
- **AND** its font-variant-numeric MUST be `tabular-nums`
- **AND** the same visual outcome MUST occur on the Detail pages

### Requirement: Compact-list baseline alignment covers both pages

`compact-list` rows in both Dashboard page and Detail pages MUST
keep `dt` (label) and `dd` (value) baseline-aligned within the
same row. Baseline alignment MUST survive uppercase transforms
and any size difference between label and value.

#### Scenario: same row dt and dd share the same line-height
- **WHEN** any Dashboard or Detail page renders a
      `compact-list` row containing a `dt` and a `dd`
- **THEN** both elements MUST resolve their `line-height` to the
      SAME `--leading-*` token (i.e. row height is shared, not
      per-element)
- **AND** the rule MUST be achieved by binding both `dt` and
      `dd` to the same `--leading-*` declaration rather than by
      coincidence (verifiable by grep)

### Requirement: Descendant-selector overrides for shared classes are removed

`apps/web/src/styles.css` MUST NOT contain any rule whose selector
exists solely to override a shared card class inside
`.dashboard-page` or `.detail-page`. The list of forbidden
selectors (which existed solely to resist cross-page leak) is:

- `.dashboard-page .compact-list dt`
- `.dashboard-page .compact-list dd`
- `.dashboard-page .metric span`
- `.dashboard-page .panel-primary`

#### Scenario: forbidden selectors are absent
- **WHEN** `apps/web/src/styles.css` is searched for any of the
      four selectors above
- **THEN** the search MUST return zero matches
- **AND** the visual behavior previously supplied by these
      selectors MUST be supplied by the base shared rule (e.g.
      `.compact-list dt`) instead
