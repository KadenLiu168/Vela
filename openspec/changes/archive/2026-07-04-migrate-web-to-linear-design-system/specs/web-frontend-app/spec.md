## MODIFIED Requirements

### Requirement: Web global design token foundation
The web frontend SHALL expose the Linear design tokens through
global CSS custom properties and use them for base page
typography, surfaces, radius, spacing, layout, and shadow
defaults; the global stylesheet SHALL adopt Linear semantic
token names.

#### Scenario: Linear color tokens are exposed
- **WHEN** a developer inspects the `:root` block of
  `apps/web/src/styles.css`
- **THEN** it declares at least the Linear color tokens
  `--color-void`, `--color-carbon`, `--color-obsidian`,
  `--color-graphite`, `--color-smoke`, `--color-ash`,
  `--color-fog`, `--color-mist`, `--color-bone`,
  `--color-paper`, `--color-acid-lime`,
  `--color-pulse-green`, `--color-coral-red`,
  `--color-signal-teal`, `--color-iris-violet`, and
  `--color-lavender`

#### Scenario: Linear typography tokens are exposed
- **WHEN** a developer inspects the `:root` block
- **THEN** it declares font families `--font-inter-variable`
  and `--font-berkeley-mono` (or the named substitute
  `--font-jetbrains-mono`); and the Linear type scale
  (`--text-caption`, `--text-body-sm`, `--text-body-lg`,
  `--text-subheading`, `--text-heading-sm`,
  `--text-heading`, `--text-heading-lg`, `--text-display`)

#### Scenario: Linear shadow tokens are exposed
- **WHEN** a developer inspects the `:root` block
- **THEN** it declares the Linear shadow tokens
  (`--shadow-sm`, `--shadow-md`, `--shadow-subtle`,
  `--shadow-subtle-2`, `--shadow-subtle-3`, `--shadow-xl`,
  `--shadow-subtle-4`, `--shadow-subtle-5`)

#### Scenario: Base page surfaces use Linear dark palette
- **WHEN** the web frontend renders any page
- **THEN** the body background uses the Linear void/carbon
  surface
- **AND** the default text color uses the Linear
  paper/bone/mist scale appropriate to the content role
- **AND** no light-theme fallback is rendered by default

### Requirement: Web frontend self-hosted font loading
The web frontend SHALL load Inter Variable and the chosen
monospace family (`JetBrains Mono` as the Berkeley Mono
substitute) from self-hosted woff2 files via `@font-face`
in `apps/web/src/styles.css`; the web frontend SHALL NOT
request fonts from Google Fonts at runtime.

#### Scenario: Inter Variable is self-hosted
- **WHEN** a developer inspects `apps/web/src/styles.css`
- **THEN** an `@font-face` block declares
  `font-family: 'Inter Variable'` and points
  `src: url('/fonts/InterVariable.woff2')`
- **AND** `apps/web/index.html` includes a
  `<link rel="preload">` for that woff2

#### Scenario: Monospace family is self-hosted
- **WHEN** a developer inspects `apps/web/src/styles.css`
- **THEN** an `@font-face` block declares
  `font-family: 'JetBrains Mono'` and points
  `src: url('/fonts/JetBrainsMono.woff2')`
- **AND** no `<link>` to Google Fonts remains in
  `apps/web/index.html`

### Requirement: Web font load validation
The web frontend SHALL continue to render text without
requiring web font network requests; `font-display: swap`
SHALL be set on every `@font-face` block so the system
fallback shows immediately.

#### Scenario: System fallback renders before web font loads
- **WHEN** a developer throttles the network in DevTools
  to "Slow 3G" and reloads any page
- **THEN** the body text is visible using the system
  fallback within the first paint
- **AND** the Inter Variable / JetBrains Mono swap
  completes once the woff2 is decoded
