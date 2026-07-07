## MODIFIED Requirements

### Requirement: Monospace font token name follows design intent

The monospace font token MUST be named after the design intent
(Berkeley Mono in the Linear reference system), not after the OFL
substitute loaded at runtime.

#### Scenario: token name is --font-berkeley-mono
- **WHEN** `tokens.css` declares the monospace family token
- **THEN** the token name MUST be `--font-berkeley-mono`
- **AND** the value MUST chain
      `'IBM Plex Mono', 'Berkeley Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`
      in that exact order
- **AND** the value's first entry (`'IBM Plex Mono'`) MUST match
      the `font-family` declared by the `@font-face` rules for the
      IBM Plex Mono woff2 files in `apps/web/src/styles.css`

#### Scenario: every consumer uses the canonical token name
- **WHEN** any CSS rule under `apps/web/src/` references the
      monospace family token
- **THEN** the reference MUST use `var(--font-berkeley-mono)`
- **AND** no CSS rule MUST use `var(--font-jetbrains-mono)`

#### Scenario: display font token is an independent semantic token
- **WHEN** `tokens.css` declares the editorial display font token
- **THEN** the token name MUST be `--font-display`
- **AND** the value MUST chain
      `'IBM Plex Mono', 'Söhne Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`
      in that exact order
- **AND** --font-display and --font-berkeley-mono MAY resolve to the
      same physical font family at runtime, distinguished by weight
      and size

#### Scenario: no JetBrains Mono @font-face is declared
- **WHEN** `apps/web/src/styles.css` is inspected
- **THEN** it MUST NOT contain an `@font-face` rule for
      `font-family: "JetBrains Mono"`
- **AND** no JetBrains Mono woff2 files exist under
      `apps/web/public/fonts/`
