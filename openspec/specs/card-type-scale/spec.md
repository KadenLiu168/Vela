# card-type-scale Specification

## Purpose
Defines the four-rung `card-type-scale` typography ladder (`meta`, `body`, `emphasis`, `display`) exposed as CSS custom properties in `tokens.css`.
## Requirements

### Requirement: Card typography ladder is exposed as four semantic rungs
The Web frontend MUST retain four quantitative/data rungs in `tokens.css`: meta `11/16px`, body/dense `13/20px`, emphasis/metric `24/30px`, and display/metric-hero `32/36px`. Card titles are a separate language role using the global card-title `16/22px` tokens. Every line-height MUST resolve through a `--leading-*` token.

#### Scenario: every ladder token is declared in tokens.css
- **WHEN** the card typography tokens are inspected
- **THEN** all four exact size/leading pairs MUST be declared
- **AND** the global card-title size/leading pair MUST also be available

#### Scenario: every card type rung is consumed by at least one rule
- **WHEN** card styles are inspected
- **THEN** every retained rung MUST have a current semantic consumer
- **AND** no dead compatibility rung MUST remain

### Requirement: Tracking tokens for meta labels and numeric emphasis
Meta labels MAY use a restrained tracking token appropriate to 11px labels. Numeric emphasis and display values MUST pair their tracking token with Mono and tabular numerals; ordinary language MUST NOT inherit numeric tracking.

#### Scenario: tracking-meta is declared and applied to meta labels
- **WHEN** a meta label uses the meta rung
- **THEN** it MUST use the shared meta tracking and leading tokens
- **AND** uppercase MUST remain limited to labels where it is already semantically useful

#### Scenario: tabular-nums pairs with tracking-numeral
- **WHEN** an emphasis or display rung renders quantitative content
- **THEN** it MUST use `--font-mono`, tabular numerals, and the numeric tracking token

### Requirement: Dashboard and Detail pages render compact-list identically
Dashboard and Detail compact lists MUST retain identical role mappings. Labels and ordinary descriptions use Sans; quantitative values, dates, symbols, parameters, and identifiers use Mono where their content semantics require it.

#### Scenario: dashboard and detail compact-list dt are identical
- **WHEN** Dashboard and Detail compact-list labels render
- **THEN** both MUST use `--font-sans`, the same 11px meta size, tracking and transform, and the shared `--leading-body-card: 20px` row leading

#### Scenario: dashboard and detail compact-list dd are identical
- **WHEN** Dashboard and Detail compact-list values render
- **THEN** both MUST use the same dense size and leading
- **AND** their family MUST be selected by content semantics rather than page ancestry

#### Scenario: dashboard and detail panel-primary are identical
- **WHEN** Dashboard and Detail primary numeric values render
- **THEN** both MUST use the metric role, `--font-mono`, and tabular numerals

### Requirement: Compact-list baseline alignment covers both pages
Compact-list rows on Dashboard and Detail pages MUST preserve label/value baseline alignment with the new Sans/Mono metrics. Both `dt` and `dd` MUST use `--leading-body-card: 20px`; this row-layout exception does not change standalone 11/16px meta labels.

#### Scenario: same row dt and dd share the same line-height
- **WHEN** a compact-list row contains an 11px Sans label and a 13px language or numeric value
- **THEN** both MUST reference `--leading-body-card` and their text baselines MUST align
- **AND** long or mixed Chinese/Latin values MUST remain contained at narrow viewports

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

### Requirement: Card titles use Sans while quantitative card values use Mono
Card titles and ordinary language inside cards MUST use `--font-sans`. Quantitative values, ETF symbols, dates, timestamps, parameters, and numeric headlines MUST use `--font-mono`; aligned numbers MUST also use `font-variant-numeric: tabular-nums`. A table or card MUST NOT force every cell into Mono when some cells contain names or descriptions.

#### Scenario: Mixed-content card preserves font semantics
- **WHEN** a card contains a title, descriptive text, an ETF symbol, and numeric values
- **THEN** the title and descriptive text MUST use Sans
- **AND** the symbol and numeric values MUST use Mono
- **AND** aligned numeric values MUST use tabular numerals

### Requirement: Card visual roles map to research typography rungs
Meta labels MUST map to meta; dense supporting data MUST map to body; primary metrics MUST map to emphasis; detail-page numeric headlines MUST map to display; card titles MUST use the separate card-title role. Descriptions and names MUST remain Sans even when adjacent to Mono data.

#### Scenario: meta label role uses meta rung
- **WHEN** a card meta label renders
- **THEN** it MUST use the 11/16px meta role and the documented label weight, except compact-list row labels use the shared 20px row leading defined below

#### Scenario: body value role uses body rung
- **WHEN** dense supporting data renders
- **THEN** it MUST use the 13/20px body/dense role

#### Scenario: emphasis role uses emphasis rung with tabular-nums
- **WHEN** a primary metric renders
- **THEN** it MUST use the 24/30px emphasis role, `--font-mono`, and tabular numerals

#### Scenario: display role uses display rung with Mono
- **WHEN** a detail-page numeric headline renders
- **THEN** it MUST use the 32/36px display role, `--font-mono`, and tabular numerals
