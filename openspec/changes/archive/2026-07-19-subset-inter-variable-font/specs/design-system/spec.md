## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Display font family token is registered

**Reason**: This historical requirement mandates an IBM Plex Mono
`@font-face`, preload, and token value, but later requirements in the same
capability require `--font-display` to resolve to Inter Variable, explicitly
forbid IBM Plex Mono resources, and define Inter Variable as the sole loaded
font. The implementation already follows the later contract.

**Migration**: Continue to use the existing `--font-display` chain headed by
`"Inter Variable"` and the sole Inter Variable `@font-face`. Do not add or
preload IBM Plex Mono.
