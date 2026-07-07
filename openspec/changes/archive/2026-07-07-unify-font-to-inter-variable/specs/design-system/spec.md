## MODIFIED Requirements

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

## ADDED Requirements

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
