## ADDED Requirements

### Requirement: Design system invariants are enforced by Stylelint
The web frontend MUST enforce the design-system invariants
already shipped in earlier changes via Stylelint. The Stylelint
config lives at `apps/web/.stylelintrc.json` and is invoked by
the `npm --prefix apps/web run lint:css` script.

The config MUST enforce, at minimum, these five rule
categories:

1. **No descendant-selector button styling.** Selectors of the
   form `.operation-list button` or any other ancestry-based
   button selector MUST be flagged.
2. **No literal numeric line-heights.** A `line-height`
   declaration whose value is a plain number or `<number><unit>`
   (e.g. `1.4`, `1.15`, `140ms`) MUST be flagged; only
   `var(...)`, `inherit`, `initial`, `unset`, `revert` are
   allowed.
3. **No literal `border-radius` pixel values.** A
   `border-radius` declaration whose value is a plain pixel
   literal (e.g. `4px`, `12px`) MUST be flagged; only `var(...)`
   and the keyword values (`inherit`, `initial`, etc.) are
   allowed.
4. **No `:root` declarations outside `tokens.css`.** A `:root`
   selector MUST NOT appear in any CSS file under
   `apps/web/src/` other than `apps/web/src/styles/tokens.css`.
5. **Acid-lime as fill is reserved.** A `background-color:
   var(--color-acid-lime)` or `outline-color:
   var(--color-acid-lime)` declaration MUST NOT appear under
   `apps/web/src/styles.css`. The CTA fill (`.button-primary`'s
   `background: var(--color-acid-lime)`) is the one place the
   fill appears and is enforced by code review (the value
   keyword differs from `background-color`). Other non-fill uses
   (focus rings via `border-color`, underlines via `box-shadow:
   inset`, text decoration via `text-decoration-color`, SVG
   `stroke` / `fill`) are intentionally allowlisted at code
   review time.

A Stylelint violation is a CI failure for rules 1–4.
Rule 5 is a lint-level rule (catches the most common misuse
patterns) plus code review (covers the allowlist).

#### Scenario: lint:css script exists and runs
- **WHEN** a developer runs `npm --prefix apps/web run lint:css`
- **THEN** the command MUST exit 0 if no design-system
      invariants are violated
- **AND** the command MUST exit non-zero with a per-file
      violation report if any rule above is violated
- **AND** the script MUST be wired into the project's CI
      pipeline (a future change may move the wiring; this
      change lands the script and config)

#### Scenario: descendant-selector button styling is flagged
- **WHEN** any CSS rule under `apps/web/src/styles.css` (or
      any future CSS file) selects a button by ancestry alone
      (e.g. `.operation-list button { ... }`)
- **THEN** `npm --prefix apps/web run lint:css` MUST exit
      non-zero and report the offending file:line

#### Scenario: literal line-height is flagged
- **WHEN** any CSS rule declares `line-height: <number>` (e.g.
      `line-height: 1.4`)
- **THEN** the lint script MUST flag it and direct the
      contributor to use a `--leading-*` token instead

#### Scenario: literal border-radius is flagged
- **WHEN** any CSS rule declares `border-radius: <number>px`
      (e.g. `border-radius: 4px`)
- **THEN** the lint script MUST flag it and direct the
      contributor to use a `--radius-*` token instead

#### Scenario: acid-lime fill misuse is flagged
- **WHEN** any CSS rule declares `background-color:
      var(--color-acid-lime)` or `outline-color:
      var(--color-acid-lime)`
- **THEN** the lint script MUST flag it and direct the
      contributor to either use `--feedback-accent-*` (for
      non-CTA accents) or restructure as `.button-primary`
      (for the per-view primary CTA). The lone legitimate
      `background: var(--color-acid-lime)` on `.button-primary`
      is the per-view primary CTA fill and is enforced by code
      review, not by this lint rule

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
The web frontend MUST ship a Markdown token reference generated
from `apps/web/src/styles/tokens.css`. The generator is at
`scripts/build-tokens-reference.mjs`, has zero runtime
dependencies (uses Node built-ins only), and is invoked by
`npm --prefix apps/web run build:tokens-doc`.

The generated output is `docs/tokens.md`. It MUST list every
token declared in the `:root { ... }` block, grouped by the
section comments already present in `tokens.css` (Colors,
Surfaces, Typography families, etc.). For each token it MUST
show the token name and its resolved value (chasing
`var(...)` aliases to a final pixel / color / numeric value).

The generated file is committed to git; subsequent edits to
`tokens.css` require re-running the generator and committing
the regenerated output.

#### Scenario: tokens.md is generated and committed
- **WHEN** a developer runs
      `npm --prefix apps/web run build:tokens-doc`
- **THEN** the file `docs/tokens.md` MUST exist and MUST
      contain one Markdown section per token group declared
      in `apps/web/src/styles/tokens.css`
- **AND** the file MUST be committed to the repository
      (verifiable via `git ls-files docs/tokens.md`)

#### Scenario: token aliases resolve to concrete values
- **WHEN** the generator encounters a token whose value is
      `var(--other-token)`
- **THEN** the Markdown output MUST show both the alias and
      the chained resolved value (e.g.
      `--space-xs: var(--spacing-8) → 8px`)

#### Scenario: generator has zero runtime dependencies
- **WHEN** `scripts/build-tokens-reference.mjs` is inspected
- **THEN** the script MUST NOT `import` or `require` any
      module other than Node built-ins
- **AND** the script MUST be invokable on a fresh `node`
      install with no `npm install` step
