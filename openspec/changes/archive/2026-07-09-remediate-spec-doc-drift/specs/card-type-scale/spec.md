## MODIFIED Requirements

### Requirement: Display font family is exposed for card titles

The web frontend MUST declare `--font-display` in
`apps/web/src/styles/tokens.css` and load a corresponding
`@font-face` rule in `apps/web/src/styles.css`. The token value
MUST chain the editorial display family `Inter Variable` first, followed by
fallbacks in this exact order:

```
--font-display: "Inter Variable", "Söhne Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
```

(Alignment note: the authoritative `design-system` capability mandates
`Inter Variable` as the served display family and forbids any `IBM Plex Mono`
`@font-face`. This capability follows that decision; the earlier
`IBM Plex Mono` wording is superseded.)

`@font-face` MUST point at a woff2 hosted under
`apps/web/public/fonts/`. The woff2 file MUST be OFL, SIL, MIT, or
Apache-2.0 licensed (no commercial-only font may be added).

`--font-display` MUST be applied to `panel-heading h3` (card
-title) and `page-heading h1` (page title). It MUST NOT be applied
to any text element below subheading size (`compact-list` dt / dd,
`metric` label / value, `panel-primary`, button text).

#### Scenario: --font-display token and @font-face are paired
- **WHEN** `apps/web/src/styles/tokens.css` is inspected
- **THEN** the `:root` block MUST declare `--font-display` with
      the chained value above (`Inter Variable` first)
- **AND** `apps/web/src/styles.css` MUST contain at least one
      `@font-face` rule whose `font-family` is the first chained
      value (`"Inter Variable"`)
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
