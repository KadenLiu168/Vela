## MODIFIED Requirements

### Requirement: Dashboard heading uses a discrete responsive ladder
Every page heading MUST use shared 36px/40px page-title tokens above 720px and shared 28px/36px compact page-title tokens at or below 720px, with approximately 580 weight. Dashboard MUST NOT introduce a divergent heading size.

#### Scenario: all pages share one heading type scale
- **WHEN** the page heading rule is inspected
- **THEN** it MUST use the shared page-title size, leading, tracking, and weight tokens without `clamp()`

#### Scenario: dashboard heading has no divergent override
- **WHEN** Dashboard styles are inspected
- **THEN** they MUST NOT override the shared heading typography

#### Scenario: mobile media query does not reintroduce a larger size
- **WHEN** responsive rules are inspected
- **THEN** they MUST NOT make Dashboard headings larger than the shared page-title role

### Requirement: Research-workstation type scale is complete
The prior marketing-scale ladder is replaced by research-workstation roles: page title `36/40` above 720px and compact page title `28/36` at or below 720px, section title `22/28`, card title `16/22`, metric hero `32/36` Mono, metric `24/30` Mono, body `15/22`, dense/table `13/20`, label `12/16`, meta `11/16`, and chart axis `11/16` Mono. All stated pixel dimensions describe computed sizes at the default 16px root font; relative units MUST allow user text enlargement. Every size and line-height MUST be declared as a token, and every CSS `line-height` consumer MUST continue to reference a `--leading-*` token.

#### Scenario: every named size is declared in tokens.css
- **WHEN** typography tokens are inspected
- **THEN** every role and exact size/line-height pair above MUST be declared

#### Scenario: --text-body and --leading-body resolve to 15px / 22px
- **WHEN** the body role is inspected after migration
- **THEN** `--text-body` MUST resolve to `15px`
- **AND** its paired leading token MUST resolve to `22px`

#### Scenario: unused --text-body-sm / --text-body-lg aliases do not regress
- **WHEN** obsolete scale aliases have no consumer
- **THEN** they MUST be removed rather than preserved as speculative compatibility tokens

#### Scenario: card-type-scale ladder is declared in tokens.css
- **WHEN** card typography is inspected
- **THEN** its data ladder MUST use the exact role mappings defined by the modified `card-type-scale` capability

#### Scenario: card-type-scale rungs map onto card visual roles
- **WHEN** text renders on a card
- **THEN** language, label, and quantitative roles MUST select the documented role token and Sans/Mono family rather than inheriting one font indiscriminately

### Requirement: Vertical rhythm between headings and content
Page headings MUST be separated from their first content surface by 24px. Section headings MUST retain 16px separation from body content. Major research sections MUST use 48px separation above 720px and 32px at or below 720px; related content groups MUST use 24px. Page and section headings MUST use Sans and shared semantic type roles.

#### Scenario: list page title is separated from main content
- **WHEN** a list page title precedes its first content surface
- **THEN** the shared 24px heading-to-content separation MUST apply

#### Scenario: detail section heading is separated from body content
- **WHEN** a detail section heading renders
- **THEN** it MUST use `--font-sans`, the section-title size/leading/weight roles, and the existing 16px bottom spacing

### Requirement: Card primitives are available as `--card-*` tokens
Standard research panels MUST use `--surface-panel`; emphasized metric cards and modal surfaces MUST use `--surface-raised`. Shared card aliases MUST retain raised surfaces and subtle borders, while standard panels MUST select the panel surface explicitly. Standard panel padding MUST be 24px on both axes; compact panels and panels at or below 720px MUST use 16px. Panel shadows MUST be absent; modal shadows MUST stay within the existing elevation vocabulary. Surface contrast plus border MUST remain the primary hierarchy mechanism.

#### Scenario: --card-* tokens are declared in tokens.css
- **WHEN** card aliases are inspected
- **THEN** `--card-bg` MUST resolve to `--surface-raised` and `--card-border-color` to `--border-subtle`
- **AND** padding, radius, gap, and optional subtle shadow MUST remain centralized

#### Scenario: --card-* tokens do not duplicate declarations
- **WHEN** other CSS files are inspected
- **THEN** they MUST consume, not redeclare, `--card-*` tokens

### Requirement: Card container padding routes through --card-padding-y

`apps/web/src/styles.css` rules that style `.dashboard-panel` (or the same class scoped to `.dashboard-page` / `.detail-page`) MUST source their `padding` (when the value is one of the canonical card paddings) through `var(--card-padding-y)` / `var(--card-padding-x)` or `var(--card-padding-compact)` rather than through bare `var(--spacing-N)` primitives.

#### Scenario: dashboard-panel padding uses card padding tokens
- **WHEN** `apps/web/src/styles.css` is searched for the rules
      targeting `.dashboard-panel`, `.dashboard-page
      .dashboard-panel`, and `.detail-page .dashboard-panel`
- **THEN** each rule's `padding` MUST resolve through
      the standard `--card-padding-y` / `--card-padding-x` tokens or the compact `--card-padding-compact` token
- **AND** no rule under these selectors MAY use a bare
      `var(--spacing-N)` for card padding

### Requirement: Research-workstation responsive presentation is preserved
The research presentation MUST retain the 1024px, 900px, and 720px breakpoint boundaries, applying the updated spacing, heading and layout contracts at those boundaries while preserving `prefers-reduced-motion` and programmatic accessibility. Wider Mono glyphs MUST NOT introduce page-level horizontal overflow or hide actions, chart labels, or Command Palette results.

#### Scenario: Required responsive states remain usable
- **WHEN** the application is reviewed above and below the existing 1024px, 900px, and 720px breakpoints
- **THEN** page headings, navigation, metric cards, tables, charts, Command Palette, and mobile full-width buttons MUST remain readable and operable
- **AND** numeric overflow MUST stay contained by the existing table/chart overflow strategy rather than producing page-level overflow

### Requirement: Motion vocabulary is declared and respected

The web frontend MUST declare a motion vocabulary in `tokens.css`
(durations and easings) and MUST honor the user's
`prefers-reduced-motion` setting.

#### Scenario: durations and easings live in tokens.css
- **WHEN** any CSS rule under `apps/web/src/` declares a
      `transition` or `animation`
- **THEN** the duration MUST come from one of `--duration-fast`
      (120ms), `--duration-base` (200ms), or `--duration-slow`
      (320ms)
- **AND** the easing MUST be `cubic-bezier(0.2, 0, 0, 1)` declared
      as `--ease-out` unless a different named token documents a
      specific need

#### Scenario: prefers-reduced-motion suppresses non-essential motion
- **WHEN** the OS reports `prefers-reduced-motion: reduce`
- **THEN** a global media query in `apps/web/src/styles.css` MUST
      set `transition-duration: 0ms` and `animation-duration: 0ms`
      on every element that uses a motion token
- **AND** non-essential motion and skeleton pulsing MUST be suppressed while textual loading feedback remains available

#### Scenario: State changes remain immediate to read
- **WHEN** a user changes a selection, opens a modal, or receives updated research data
- **THEN** hover feedback MUST use 120ms, optional modal transitions MUST use 200ms, and optional disclosure transitions MUST not exceed 200ms
- **AND** values MUST NOT count up, chart results MUST NOT wait for a drawing animation, and cards MUST NOT use staggered entrance motion
- **AND** updates MUST retain reading position except for existing navigation focus behavior

## ADDED Requirements

### Requirement: Research layout and control dimensions have semantic tokens
The canonical token source MUST declare page gutters of 32px above 1024px, 24px from 721px through 1024px, and 16px at or below 720px; major section spacing of 48px/32px for desktop/mobile; group and heading-content spacing of 24px; standard/compact panel padding of 24px/16px; desktop control minimum height of 36px and touch control minimum height of 44px. These sizes are default-root computed values and MUST scale with user text settings. These dimensions MUST be consumed by their corresponding roles without competing token roots. The 1200px maximum content width and existing radius mapping MUST remain unchanged.

#### Scenario: Narrow layout applies compact dimensions
- **WHEN** a research page renders at 390px width
- **THEN** its page gutters MUST be 16px, panel padding 16px, and major section separation 32px
- **AND** controls MUST have at least 44px height, wrapping labels instead of clipping them

#### Scenario: Desktop layout uses standard dimensions
- **WHEN** a research page renders at 1440px width
- **THEN** page gutters MUST be 32px, standard panel padding 24px, and major section separation 48px
- **AND** desktop controls MUST have at least 36px height; coarse-pointer controls MUST retain at least 44px height

### Requirement: Component states share readable visual treatment
Navigation, buttons, inputs, filters, tables, feedback and palette results MUST distinguish every applicable default, hover, focus, active, selected, disabled, loading and error state. Selection MUST be programmatically exposed. Pending buttons MUST retain a stable minimum width and visible operation text; field errors MUST be associated with the affected input. Status and risk information MUST remain readable at 13px/20px or larger; important supporting dates and evidence counts MUST use at least the shared 12px/16px label role. Ordinary meta labels retain the established meta role.

#### Scenario: Pending and failed form submission
- **WHEN** an existing form submits or fails validation
- **THEN** pending controls MUST remain identifiable without width collapse, existing duplicate-submission protection MUST remain, and error text MUST identify the affected field programmatically

#### Scenario: State catalog covers actual consumers
- **WHEN** shared visual states are reviewed
- **THEN** the component catalog MUST demonstrate buttons, inputs, panels, mixed-content tables and feedback with applicable states
- **AND** disabled and loading states MUST remain distinguishable without relying solely on opacity or color

