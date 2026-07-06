## ADDED Requirements

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
