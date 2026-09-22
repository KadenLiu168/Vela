# design-system Specification

## Purpose
Defines the canonical web design-token system: every CSS custom property lives in `apps/web/src/styles/tokens.css` as a single `:root` block, wired via `@import` and referenced through `var(--*)`.
## Requirements

### Requirement: Design tokens live in a single canonical file
The canonical on-disk source of design tokens for the Web frontend MUST be `apps/web/src/styles/tokens.css`. The file MUST contain a single `:root { ... }` block declaring every design token used by the frontend.

#### Scenario: tokens.css is imported by the stylesheet
- **WHEN** the Web app builds
- **THEN** `apps/web/src/styles.css` MUST import `./styles/tokens.css` before rules that consume its tokens
- **AND** no other CSS file under `apps/web/src/` MUST declare a `:root` token block

#### Scenario: introducing a competing token declaration is non-conforming
- **WHEN** another CSS file declares a design token in `:root`
- **THEN** the declaration MUST be rejected as a competing source of truth

#### Scenario: token catalog is the documented source of truth
- **WHEN** a developer inspects the token catalog
- **THEN** its leading comment MUST list semantic Surfaces, Borders, Text, Interaction, Status, China market, Charts, Typography, Spacing, Radius, Shadow, Layout, Motion, and shared component aliases

### Requirement: Implementation-only tokens live in tokens.css
All semantic design tokens, including status aliases and `--focus-ring-color`, MUST live in `tokens.css`. Transitional `--feedback-accent-*` aliases MAY exist only in `tokens.css` while consumers are migrated and MUST resolve to `--status-*`; the completed change MUST remove an alias that has no remaining consumer.

#### Scenario: feedback accents resolve to the named palette tokens
- **WHEN** a feedback alias is retained during migration
- **THEN** it MUST resolve to the matching `--status-*` source role
- **AND** ordinary component rules MUST prefer the source status token directly

#### Scenario: focus ring uses --focus-ring-color
- **WHEN** an element receives `:focus-visible`
- **THEN** its outline color MUST use `var(--focus-ring-color)` resolving to `#87a4ff`

#### Scenario: card and pill radii use the named aliases
- **WHEN** card and pill elements render
- **THEN** their existing `--radius-cards` and `--radius-pills` mappings MUST remain unchanged

### Requirement: Token and component changes flow through OpenSpec
Any addition, removal, rename, or value change to a canonical design token or documented component contract MUST be declared by an active, strict-valid OpenSpec Change before implementation. Implementation, review, and verification occur while the Change is active; archive occurs only after the implementation is accepted.

#### Scenario: adding a new token requires an OpenSpec change
- **WHEN** a new token is needed
- **THEN** an active Change MUST declare its name, value, role, and affected consumers before it appears in `tokens.css`
- **AND** archive MUST NOT be treated as an implementation prerequisite

#### Scenario: renaming a token requires a same-change migration
- **WHEN** an existing token is renamed
- **THEN** declarations, consumers, specs, tests, and generated documentation MUST migrate in the same Change
- **AND** the old name MUST be absent before archive

### Requirement: Buttons follow a three-variant contract
Every Web button MUST remain exactly one of `primary`, `secondary`, or `tertiary`. Operation groups MUST remain secondary except for the single view-level primary CTA.

#### Scenario: primary button uses the accent fill
- **WHEN** a button declares `primary`
- **THEN** its resting, hover, and pressed fills MUST use the three `--interactive-primary*` tokens
- **AND** its foreground MUST use `--surface-canvas`

#### Scenario: secondary button is outline-only
- **WHEN** a button declares `secondary`
- **THEN** it MUST use a transparent or subtle surface, `--border-subtle`, and `--text-secondary`

#### Scenario: tertiary button is text-only
- **WHEN** a button declares `tertiary`
- **THEN** it MUST have no visual chrome and transition from `--text-secondary` to `--text-primary`

#### Scenario: buttons in one operation group share a tier
- **WHEN** an operation group contains multiple buttons
- **THEN** all MUST be secondary except the single explicitly designated view-level primary CTA

### Requirement: Secondary buttons render a selected state when pressed
A pressed secondary button MUST expose selection through `aria-pressed="true"` and a semantic selected treatment without becoming another primary CTA.

#### Scenario: pressed secondary button uses the inverted fill
- **WHEN** a secondary button has `aria-pressed="true"`
- **THEN** its selected surface MUST use `--surface-hover`, its border MUST use `--border-strong`, and its text MUST use `--text-primary`

#### Scenario: selection controls declare a variant className
- **WHEN** a single-select filter renders buttons
- **THEN** every option MUST carry exactly one existing button variant class
- **AND** selection MUST remain programmatically exposed through `aria-pressed`

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
- **AND** non-essential motion MUST be suppressed; loading spinners
      driven by user-initiated actions MAY remain

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

### Requirement: Buttons declare their variant via className
Every `<button>` (or `[role="button"]`) in `apps/web/src/` MUST
carry a className of the exact form `button-primary`,
`button-secondary`, or `button-tertiary` to advertise its variant
to CSS and tooling. The visual treatment carried by each class
is the one declared under "Buttons follow a three-variant
contract" in the `design-system` capability.

#### Scenario: every styled button has a variant className
- **WHEN** any HTML element under `apps/web/src/` carries the role
      of an actionable button (`<button>`, `[role="button"]`,
      `<input type="button">`, `<input type="submit">`)
- **THEN** its className MUST include one of the literal class
      tokens `button-primary`, `button-secondary`, or
      `button-tertiary`
- **AND** it MUST NOT include more than one variant class

#### Scenario: variant class is the only carrier of visual treatment
- **WHEN** a CSS rule under `apps/web/src/styles.css` declares a
      visual property for buttons (background, color, border,
      box-shadow, or font-weight)
- **THEN** the rule's selector MUST begin with one of the three
      `.button-primary`, `.button-secondary`, `.button-tertiary`
      class selectors (or a documented descendant of one of them)
- **AND** no rule MUST select buttons by ancestry alone
      (e.g. `.operation-list button`)

#### Scenario: third-party buttons get a variant too
- **WHEN** any third-party component (e.g. `EmptyAction`,
      `FeedbackMessage`) renders a button on behalf of the web
      frontend
- **THEN** the rendered DOM MUST include the appropriate variant
      className on the button (either inside the component or at
      the call site)

### Requirement: Spacing uses an 8px-grid semantic ladder
The web frontend MUST expose a semantic spacing ladder as the
first-class way to express layout gaps, and the ladder MUST
resolve to multiples of 8 (8 / 16 / 24 / 32 / 48 / 64 / 96 px).
The ladder is declared in `apps/web/src/styles/tokens.css` as the
following aliases:

- `--space-xs` resolves to `8px`
- `--space-sm` resolves to `16px`
- `--space-md` resolves to `24px`
- `--space-lg` resolves to `32px`
- `--space-xl` resolves to `48px`
- `--space-2xl` resolves to `64px`
- `--space-3xl` resolves to `96px`

Each `--space-*` alias MUST be implemented as
`var(--spacing-N)` onto an existing 8px-grid primitive
(`--spacing-8 / --spacing-16 / --spacing-24 / --spacing-32 /
--spacing-48 / --spacing-64 / --spacing-96`).

The `--spacing-N` primitives remain available for fine-grained
borders, padding-edge nudges, and any value that does not
fit the 8px-grid ladder. New layout-gap code SHOULD prefer
`--space-*`.

#### Scenario: --space-* ladder is declared in tokens.css
- **WHEN** a developer inspects `apps/web/src/styles/tokens.css`
- **THEN** the `:root` block MUST declare `--space-xs`,
      `--space-sm`, `--space-md`, `--space-lg`, `--space-xl`,
      `--space-2xl`, `--space-3xl`
- **AND** each MUST resolve (transitively) to one of
      `8px`, `16px`, `24px`, `32px`, `48px`, `64px`, `96px`

#### Scenario: layout gaps use --space-* rather than ad-hoc spacing-N
- **WHEN** any CSS rule under `apps/web/src/styles.css` sets
      a layout-gap property (`gap`, `margin`, or `padding`) on a
      top-level page section, panel, or list
- **THEN** the value SHOULD resolve through `var(--space-*)`
- **AND** the literal value MUST NOT exceed `96px` (the top
      rung of the ladder) without an explicit override

#### Scenario: pre-existing dead --spacing-28 / --spacing-140 are pruned
- **WHEN** `tokens.css` is searched for the declared
      `--spacing-28` and `--spacing-140` primitives
- **THEN** neither token MUST be declared
- **AND** both `--spacing-28` and `--spacing-140` MUST be absent
      from every CSS file under `apps/web/src/` (verified by
      `grep -RE "var\(--spacing-(28|140)\)" apps/web/src/`
      returning no matches before deletion)
- **AND** every other declared `--spacing-N` primitive that is
      NOT one of the seven backing primitives
      (`--spacing-8 / 16 / 24 / 32 / 48 / 64 / 96`) MAY remain
      declared even if it currently has zero `var(...)`
      consumers; pruning those pre-existing dead primitives is
      out of scope for this change

### Requirement: Card primitives are available as `--card-*` tokens
Shared card aliases MUST resolve to `--surface-raised`, `--border-subtle`, existing spacing/radius tokens, and no shadow stronger than the existing subtle elevation vocabulary. Surface contrast plus border MUST remain the primary hierarchy mechanism.

#### Scenario: --card-* tokens are declared in tokens.css
- **WHEN** card aliases are inspected
- **THEN** `--card-bg` MUST resolve to `--surface-raised` and `--card-border-color` to `--border-subtle`
- **AND** padding, radius, gap, and optional subtle shadow MUST remain centralized

#### Scenario: --card-* tokens do not duplicate declarations
- **WHEN** other CSS files are inspected
- **THEN** they MUST consume, not redeclare, `--card-*` tokens

### Requirement: Radius → component mapping is canonical
The web frontend MUST follow a documented mapping between each
component family and a single radius token. The mapping is:

- **Card** (`.panel-primary`, `.dashboard-card`, `.metric-card`,
  and similar surfaces) → `var(--radius-cards)` (12 px)
- **Button** (`.button-primary`, `.button-secondary`,
  `.button-tertiary`) → `var(--radius-buttons)` (6 px)
- **Input** (`input`, `select`, `textarea`) →
  `var(--radius-inputs)` (6 px)
- **Badge** (numeric / status badges) →
  `var(--radius-badges)` (4 px)
- **Navigation chrome** (`.app-nav`, `.app-nav-link`) →
  `var(--radius-md)` (6 px). Navigation chrome is NOT a pill.
- **Pill** (true pill-shaped chrome: `--radius-pills: 9999px`)
  is reserved for badge / tag components and MUST NOT be used
  on navigation chrome

Components not in this list SHOULD consume the closest primitive
(`--radius-sm` 2 px, `--radius-md` 6 px, `--radius-xl` 12 px,
`--radius-2xl` 16 px) and document the choice in their CSS rule.

#### Scenario: navigation chrome is not a pill
- **WHEN** `apps/web/src/styles.css` is searched for the
      `.app-nav-link` rule
- **THEN** its `border-radius` MUST resolve to `var(--radius-md)`
      (or any non-pill radius token — `--radius-sm`,
      `--radius-md`, `--radius-buttons`, `--radius-cards`)
- **AND** it MUST NOT resolve to `var(--radius-pills)` or
      `var(--radius-full)` or `var(--radius-full-2)`

#### Scenario: nav container is not a pill
- **WHEN** `apps/web/src/styles.css` is searched for the
      `.app-nav` rule
- **THEN** its `border-radius` MUST resolve to a non-pill
      radius token (`--radius-sm`, `--radius-md`,
      `--radius-buttons`, `--radius-cards`)
- **AND** it MUST NOT resolve to `var(--radius-pills)` or
      `var(--radius-full)` or `var(--radius-full-2)`

#### Scenario: button rules use --radius-buttons
- **WHEN** any CSS rule under `apps/web/src/styles.css` styles
      a `.button-primary`, `.button-secondary`, or
      `.button-tertiary` element
- **THEN** its `border-radius` MUST come from
      `var(--radius-buttons)`

#### Scenario: card surfaces use --radius-cards
- **WHEN** any CSS rule under `apps/web/src/styles.css` styles
      a card surface (`.panel-primary`, `.dashboard-card`,
      `.metric-card`, `.equity-curve-card`, or analogous
      surface)
- **THEN** its `border-radius` MUST come from
      `var(--radius-cards)`

### Requirement: Dashboard heading uses a discrete responsive ladder
Every page heading MUST use the shared 36px/40px page-title tokens and approximately 580 weight. Dashboard MUST NOT introduce a divergent heading size.

#### Scenario: all pages share one heading type scale
- **WHEN** the page heading rule is inspected
- **THEN** it MUST use the shared page-title size, leading, tracking, and weight tokens without `clamp()`

#### Scenario: dashboard heading has no divergent override
- **WHEN** Dashboard styles are inspected
- **THEN** they MUST NOT override the shared heading typography

#### Scenario: mobile media query does not reintroduce a larger size
- **WHEN** responsive rules are inspected
- **THEN** they MUST NOT make Dashboard headings larger than the shared page-title role

### Requirement: State component set is exported from the components barrel
The web frontend MUST expose the Empty / Loading / Skeleton /
Error state-UI primitives as a single named family that is
importable from `apps/web/src/components` (the canonical barrel
at `apps/web/src/components/index.ts`).

The family is:

- **`EmptyState`** — paragraph-shaped empty surface
  (`<p class="status-surface status-surface-empty empty-state">`)
  for "no data yet" or "nothing matches" states
- **`FeedbackMessage`** — banner-shaped status surface
  (`<div role="status" | "alert" class="status-surface
  feedback-message feedback-message-{variant}">`) for the
  `loading | success | error | info` variants
- **`Skeleton`** — placeholder primitive for content whose
  shape is known but whose data is still loading. Renders an
  element with the `.skeleton` class plus optional
  `.skeleton-pulse` animation
- **`ErrorBoundary`** — React class component that catches
  render-time exceptions in its `children` subtree and renders
  a `<FeedbackMessage variant="error">` fallback

All four components MUST be re-exported by
`apps/web/src/components/index.ts`. New code MUST import the
state components from this barrel rather than from the
underlying files.

#### Scenario: barrel exports the four state components
- **WHEN** a developer inspects `apps/web/src/components/index.ts`
- **THEN** the file MUST re-export `EmptyState`,
      `FeedbackMessage`, `Skeleton`, and `ErrorBoundary` as
      named exports
- **AND** any page or test under `apps/web/src/` that needs
      a state component MUST import from
      `"../components"` (or the equivalent relative path that
      resolves to the barrel) rather than from the underlying
      component files

#### Scenario: Skeleton pulse respects prefers-reduced-motion
- **WHEN** the OS reports `prefers-reduced-motion: reduce`
- **THEN** any `<Skeleton>` element with the `.skeleton-pulse`
      class MUST NOT animate (its `animation` property MUST
      resolve to `none` and its `opacity` MUST remain constant)
- **AND** the placeholder MUST still be visually present
      (the surface color and dimensions are preserved)

#### Scenario: ErrorBoundary renders a feedback-message-error fallback on child errors
- **WHEN** a child component passed to `<ErrorBoundary>`
      throws a render-time exception
- **THEN** the boundary MUST render a
      `<FeedbackMessage variant="error">` element (or the
      `fallback` prop if provided) in place of the failing
      subtree
- **AND** the rest of the AppShell (header, nav, main
      layout) MUST continue to render normally

#### Scenario: Skeleton default is inline span
- **WHEN** a `<Skeleton />` element is rendered without props
- **THEN** it MUST render as an inline `<span>` element
- **AND** its rendered width MUST default to `100%` of its
      containing inline context
- **AND** its rendered height MUST default to `0.75em` (one
      line of body text)

### Requirement: Design system invariants are enforced by Stylelint
Stylelint MUST continue to reject ancestry-only button styling, literal line-heights, and literal border-radius values. The existing separate canonical-root guard and concentrated static tests MUST reject competing `:root` blocks; final validation MUST explicitly execute that guard. The legacy acid-lime rule MUST be replaced by enforcement that component CSS does not use removed visual tokens or literal palette colors and that interaction, status, market, and chart semantic families are not substituted for their documented roles where statically enforceable.

#### Scenario: lint:css script exists and runs
- **WHEN** `npm --prefix apps/web run lint:css` runs
- **THEN** it MUST fail on configured design-system violations and pass conforming source

#### Scenario: descendant-selector button styling is flagged
- **WHEN** a button is styled only by ancestry
- **THEN** CSS lint MUST report it

#### Scenario: literal line-height is flagged
- **WHEN** a rule uses a literal line-height
- **THEN** CSS lint MUST direct the contributor to a `--leading-*` token

#### Scenario: literal border-radius is flagged
- **WHEN** a rule uses a literal radius
- **THEN** CSS lint MUST direct the contributor to a radius token

#### Scenario: acid-lime fill misuse is flagged
- **WHEN** source uses a removed acid-lime token or a literal palette hex outside `tokens.css`
- **THEN** automated static checks MUST fail and direct the contributor to the appropriate semantic family

### Requirement: Component catalog is reachable via Ladle
The web frontend MUST expose a dev-only component catalog that
renders each state component with controls for its variant /
shape / width / height props. The catalog is implemented with
`@ladle/react`, configured at `apps/web/.ladle/config.mjs`,
and started via the `npm --prefix apps/web run ladle` script.

A story MUST exist for each state component in
`apps/web/src/components/`:

- `FeedbackMessage.stories.tsx` — one story per variant
  (`loading | success | error | info`) plus a default
- `Skeleton.stories.tsx` — text default, block shape, circle
  variant with diameter variations
- `ErrorBoundary.stories.tsx` — happy path, default fallback,
  custom fallback prop
- `EmptyState.stories.tsx` — empty state with default content,
  and one paired with `EmptyAction`

The catalog is dev-only and MUST NOT contribute to the
production bundle.

#### Scenario: ladle script exists and starts the dev catalog
- **WHEN** a developer runs `npm --prefix apps/web run ladle`
- **THEN** a local dev server MUST start on
      `http://localhost:61000` (or a documented alternative
      port)
- **AND** the catalog MUST list a story for each of the four
      state components
- **AND** each story MUST render the component with its
      documented props wired to Ladle controls

#### Scenario: stories use the production components directly
- **WHEN** any `.stories.tsx` file under
      `apps/web/src/components/` renders a component
- **THEN** the rendered element MUST be the actual production
      component (imported from the same module the app uses),
      not a re-implementation or a mock
- **AND** the production build (`npm --prefix apps/web run
      build`) MUST NOT include any `.stories.tsx` file in the
      bundle (Vite / Ladle handle this separation)

### Requirement: Token reference doc is generated from tokens.css
The zero-dependency generator MUST continue to produce `docs/tokens.md` from `tokens.css`, including alias resolution and all new semantic groups. The generated file MUST be tracked despite the repository's broader local-doc ignore policy.

#### Scenario: tokens.md is generated and committed
- **WHEN** the token-doc command runs
- **THEN** `docs/tokens.md` MUST match the current canonical tokens and be unignored during implementation
- **AND** after explicitly authorized delivery it MUST be present in `git ls-files`; implementation validation MUST NOT itself require staging or committing

#### Scenario: token aliases resolve to concrete values
- **WHEN** a token aliases another token
- **THEN** the generated reference MUST show both the alias and resolved value

#### Scenario: generator has zero runtime dependencies
- **WHEN** the generator is inspected
- **THEN** it MUST use only Node built-ins

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

### Requirement: Low-contrast palette colors are not readable text colors
Ordinary readable text MUST use `--text-primary`, `--text-secondary`, or `--text-tertiary` only where the rendered foreground/background pair meets WCAG AA. Status text, market-direction figures, and chart identity labels MAY use their corresponding semantic token family when that pair meets WCAG AA. Because `--text-tertiary` on `--surface-hover` is below 4.5:1, hover and active rows containing readable tertiary metadata MUST promote that metadata to at least `--text-secondary`.

#### Scenario: readable text avoids ash and smoke
- **WHEN** readable text is styled
- **THEN** it MUST use a semantic text token or an appropriate status, market, or chart identity token meeting WCAG AA

#### Scenario: command palette metadata remains readable
- **WHEN** a Command Palette row is hovered or active
- **THEN** readable metadata on `--surface-hover` MUST use at least `--text-secondary`

#### Scenario: neutral status text remains readable
- **WHEN** a neutral or empty status renders
- **THEN** its text MUST meet WCAG AA on its rendered surface

#### Scenario: decorative uses may stay subdued
- **WHEN** a border, grid line, or non-informational separator is subdued
- **THEN** it MAY use border/chart structural tokens and MUST NOT become the sole carrier of information

### Requirement: Vertical rhythm between headings and content
Existing heading-to-content spacing contracts MUST remain unchanged, but page and section headings MUST use `--font-sans` and their new semantic type roles.

#### Scenario: list page title is separated from main content
- **WHEN** a list page title precedes its first content surface
- **THEN** the existing `--space-xl` separation MUST remain

#### Scenario: detail section heading is separated from body content
- **WHEN** a detail section heading renders
- **THEN** it MUST use `--font-sans`, the section-title size/leading/weight roles, and the existing 16px bottom spacing

### Requirement: Categorical multi-series color palette
The chart palette MUST declare `--chart-series-1: #7c9cff`, `--chart-series-2: #46c2b3`, `--chart-series-3: #f3c969`, `--chart-series-4: #d88cff`, `--chart-series-5: #ff8a65`, and `--chart-series-6: #8fcb6a`. Strategy, equal-weight monthly, and CSI 300 buy-and-hold MUST map to series 1, 2, and 3 by stable key; unknown keys MUST deterministically map to roles 4–6.

#### Scenario: Palette declares exact controlled tokens
- **WHEN** chart tokens are inspected
- **THEN** all six exact series tokens MUST be declared in `tokens.css`

#### Scenario: Series color maps stably by key
- **WHEN** a supported or unknown series is resolved
- **THEN** resolution MUST depend on its key rather than array position or sibling presence

#### Scenario: Direct-label colors remain readable
- **WHEN** a series color is used for text
- **THEN** it MUST meet WCAG AA on the rendered chart surface
- **AND** a textual legend or label MUST still communicate identity

#### Scenario: Tokens stay in the single canonical file
- **WHEN** series tokens are declared
- **THEN** declarations MUST exist only in canonical `tokens.css`

### Requirement: Semantic color roles are independent
The design system MUST declare the following exact semantic color roles in the canonical `tokens.css` source:

- surfaces: `--surface-canvas: #090c12`, `--surface-panel: #0f141d`, `--surface-raised: #151c28`, `--surface-hover: #1c2533`
- borders: `--border-subtle: #263244`, `--border-strong: #35445a`
- text: `--text-primary: #f4f7fb`, `--text-secondary: #b7c0ce`, `--text-tertiary: #7f8a9a`
- interaction: `--interactive-primary: #6d8eff`, `--interactive-primary-hover: #87a4ff`, `--interactive-primary-pressed: #587af2`, `--focus-ring-color: #87a4ff`
- status: `--status-success: #45d483`, `--status-warning: #f6c85f`, `--status-danger: #ff5c7a`, `--status-info: #52c7ea`
- China market: `--market-up: #ff7a59`, `--market-down: #2fc6a2`, `--market-flat: #b7c0ce`
- chart primitives: `--chart-primary-line: #7c9cff`, `--chart-grid: #263244`, `--chart-axis: #7f8a9a`, `--chart-crosshair: #7f8a9a`

Components MUST consume these semantic roles rather than color-named or component-specific palette tokens. Interaction, status, market, and chart roles MUST NOT substitute for one another even when their rendered hues are similar.

#### Scenario: Components consume semantic roles
- **WHEN** CSS and inline SVG styles under `apps/web/src/` are inspected
- **THEN** surfaces, borders, readable text, interactions, feedback, market movement, and chart marks MUST reference the corresponding semantic token family
- **AND** component-specific palette tokens and literal palette hex values MUST NOT appear outside `tokens.css`

#### Scenario: Legacy visual tokens are absent
- **WHEN** the completed Web source is searched for legacy `color-(void|carbon|obsidian|graphite|smoke|ash|fog|mist|bone|paper|acid-lime|pulse-green|coral-red|signal-teal|iris-violet|lavender)`, `surface-(void|carbon|obsidian|slate)`, or `color-series-*` tokens
- **THEN** no runtime declaration or consumer MUST remain under `apps/web/src/`
- **AND** test fixtures naming forbidden tokens solely to verify rejection are permitted and MUST NOT be bundled into runtime code

### Requirement: System feedback and China-market direction remain separate
Loading, ready, success, warning, error, and information states MUST resolve through the status vocabulary. Empty/neutral surfaces MUST use readable text and neutral border roles without implying an operational outcome. Positive, negative, and flat investment returns MUST resolve through the China-market vocabulary, where positive is red, negative is green, and flat is neutral. A status token MUST NOT encode market direction, and a market token MUST NOT encode operational state.

#### Scenario: Feedback uses status roles
- **WHEN** a feedback message, load state, error surface, success result, warning, or informational state renders
- **THEN** its accent MUST originate from `--status-success`, `--status-warning`, `--status-danger`, or `--status-info`
- **AND** it MUST NOT use any `--market-*` or `--interactive-*` token

#### Scenario: Returns use China-market roles
- **WHEN** a positive, negative, or neutral return is rendered with directional color
- **THEN** it MUST use `--market-up`, `--market-down`, or `--market-flat` respectively
- **AND** the direction MUST remain available through text, sign, or another non-color cue

### Requirement: Geist Sans and Geist Mono are real runtime families
The Web frontend MUST load Geist Sans Variable and Geist Mono Variable as distinct project-hosted WOFF2 families. `--font-sans` MUST resolve first to `"Geist Sans"` and provide Chinese and system sans fallbacks; `--font-mono` MUST resolve first to `"Geist Mono"` and provide system monospace fallbacks. Body, navigation, buttons, headings, descriptions, labels, ordinary table text, and status messages MUST use Sans. Prices, percentages, returns, dates, timestamps, ETF symbols, parameters, API metadata, metrics, numeric table cells, chart axes, and code-like data MUST use Mono and MUST use tabular numerals where column alignment matters.

#### Scenario: Dual font roles load independently
- **WHEN** `tokens.css`, the global stylesheet, and the built page are inspected
- **THEN** `--font-sans` and `--font-mono` MUST be declared and consumed
- **AND** separate normal-style variable WOFF2 `@font-face` rules MUST load `"Geist Sans"` and `"Geist Mono"`
- **AND** both referenced resources MUST exist in the production build

#### Scenario: Legacy font aliases are absent
- **WHEN** `apps/web/src/` is searched after migration
- **THEN** `--font-inter-variable`, `--font-display`, and `--font-berkeley-mono` MUST have no runtime declarations or consumers; negative-test fixtures may name them solely to verify rejection

#### Scenario: Language and data roles use the intended family
- **WHEN** representative headings, descriptions, numeric metrics, ETF symbols, dates, tables, charts, and Command Palette values render
- **THEN** language/UI roles MUST resolve through `--font-sans`
- **AND** quantitative or code-like roles MUST resolve through `--font-mono`
- **AND** ordinary names and descriptions MUST NOT be forced into Mono merely because they share a row with numeric data

### Requirement: Vendored Geist resources are pinned and licensed
The two runtime fonts MUST come from the official Geist v1.7.2 distribution, retain the official OFL-1.1 notice, and be reproducibly identifiable by source URL, release tag, filename, and SHA-256. The Sans WOFF2 SHA-256 MUST be `2ffebe993e969069a9789d15164b7715d42491b5835516c5e3b935d5f81b05f1`; the Mono WOFF2 SHA-256 MUST be `afaacc4c5fbba89d2ebf7a02dc4070208540874592a5504d57175782fe893101`. Both MUST expose a `wght` axis covering 100–900; the CSS range MAY be narrowed to the weights Vela consumes.

#### Scenario: Font provenance is verifiable
- **WHEN** the committed font resources and provenance material are inspected
- **THEN** the two WOFF2 hashes, official v1.7.2 source, and OFL-1.1 notice MUST match this requirement
- **AND** no Inter font resource or Inter-only subset input MUST remain in the runtime or font-generation source directories

#### Scenario: Both first-screen families are preloaded
- **WHEN** `apps/web/index.html` and the global `@font-face` rules are inspected
- **THEN** exactly two font preloads MUST exist, one for the Sans resource and one for the Mono resource
- **AND** each preload URL MUST equal its corresponding `@font-face` URL

#### Scenario: Font replacement preserves usable fallback and loading
- **WHEN** mixed Chinese/Latin text, digits, punctuation, minus, arrows, and UI symbols render
- **THEN** supported glyphs MUST use the intended Geist family and other glyphs MUST have a usable system fallback
- **AND** both faces MUST retain `font-display: swap` without an obsolete Inter subset range
- **AND** font tests MUST inspect the actual binaries and the browser review MUST verify both loaded faces and fallback rendering

### Requirement: Celestial Blue is reserved for interaction identity
Celestial Blue MUST express primary actions, interactive selection, focus, active interaction, and product identity. It MUST NOT express success, error, market movement, generic chart identity, or loading merely because a state needs color. A rendered view MUST continue to present at most one prominent primary CTA.

#### Scenario: Primary interaction uses Celestial Blue
- **WHEN** a primary button renders in its resting, hover, or pressed state
- **THEN** it MUST use `--interactive-primary`, `--interactive-primary-hover`, or `--interactive-primary-pressed` respectively
- **AND** its foreground MUST remain a dark semantic surface color with WCAG AA contrast

#### Scenario: Focus remains visible
- **WHEN** an interactive element receives `:focus-visible`
- **THEN** its outline MUST use `--focus-ring-color`
- **AND** the focus indication MUST remain clearly distinguishable from adjacent surfaces

### Requirement: Research-workstation responsive presentation is preserved
The semantic color and typography migration MUST preserve the existing 1024px, 900px, and 720px responsive behavior, `prefers-reduced-motion`, and programmatic accessibility. Wider Mono glyphs MUST NOT introduce page-level horizontal overflow or hide actions, chart labels, or Command Palette results.

#### Scenario: Required responsive states remain usable
- **WHEN** the application is reviewed above and below the existing 1024px, 900px, and 720px breakpoints
- **THEN** page headings, navigation, metric cards, tables, charts, Command Palette, and mobile full-width buttons MUST remain readable and operable
- **AND** numeric overflow MUST stay contained by the existing table/chart overflow strategy rather than producing page-level overflow

### Requirement: Monospace typography uses the Geist Mono semantic role
The monospace token MUST be named for its semantic role as `--font-mono`; its first runtime family MUST be `"Geist Mono"`. Consumers MUST select it because content is quantitative or code-like, not because a component historically used a display-font alias.

#### Scenario: token name is --font-mono
- **WHEN** `tokens.css` declares the monospace family token
- **THEN** the canonical token MUST be `--font-mono`
- **AND** its fallback chain MUST be `"Geist Mono", "SFMono-Regular", "Cascadia Mono", "Roboto Mono", Menlo, Monaco, Consolas, monospace`

#### Scenario: every consumer uses the canonical token name
- **WHEN** a CSS rule requests monospace typography
- **THEN** it MUST use `var(--font-mono)`
- **AND** no legacy font-family token MAY remain

### Requirement: Research-workstation type scale is complete
The prior marketing-scale ladder is replaced by research-workstation roles: page title `36/40`, section title `22/28`, card title `16/22`, metric hero `32/36` Mono, metric `24/30` Mono, body `15/22`, dense/table `13/20`, label `12/16`, meta `11/16`, and chart axis `11/16` Mono. Every size and line-height MUST be declared as a token, and every CSS `line-height` consumer MUST continue to reference a `--leading-*` token.

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
