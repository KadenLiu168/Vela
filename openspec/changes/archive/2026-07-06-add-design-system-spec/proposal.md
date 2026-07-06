## Why

The Vela web frontend currently has three problems that, together,
prevent the design system from being a first-class capability:

1. `DESIGN.md` and `tokens.json` were deleted from the repo root
   without a successor, leaving no human-readable token reference.
2. `variables.css` (the CSS-side token catalog) was edited in isolation
   today (`--font-jetbrains-mono` → `--font-berkeley-mono`) but is
   **not imported by `apps/web/src/main.tsx`**. The active runtime
   tokens live in a `:root { ... }` block inside `apps/web/src/styles.css`
   that has silently forked from the reference — exactly the drift
   called out in the parent Initiative "Align Vela Web with Design
   System + Tokenize Implementation" (issue F-305).
3. There is no OpenSpec capability owning "design tokens" or any other
   visual rule, so any future edit to a token or component lives
   outside the spec-driven workflow.

This change promotes design-system into a top-level capability and
makes `apps/web/src/styles/tokens.css` the canonical on-disk source of
design tokens, so every future token or component change must flow
through an OpenSpec change proposal.

## What Changes

- **Add new OpenSpec capability `design-system`** at
  `openspec/specs/design-system/spec.md`, organized under three
  requirement groups: Tokens, Components, and Motion.
- **Move** `/variables.css` to `apps/web/src/styles/tokens.css`. The
  file becomes the canonical on-disk source of design tokens for the
  web frontend and lives inside the package that consumes it.
- **Fold** the implementation-only tokens that today live only in
  `apps/web/src/styles.css :root` into `tokens.css`: `--text-micro`,
  `--text-label`, `--text-body`, `--leading-body`, every
  `--feedback-accent-*`, `--focus-ring-color`, `--radius-cards`,
  `--radius-pills`, and `--surface-slate`.
- **Replace** the `:root { ... }` block in `apps/web/src/styles.css`
  with `@import "./tokens.css"` (resolved relative to
  `apps/web/src/styles/`), so styles.css no longer declares any CSS
  custom property.
- **Rename** the monospace font token from `--font-jetbrains-mono` to
  `--font-berkeley-mono` and chain its value to
  `'JetBrains Mono', 'Berkeley Mono', ui-monospace, ...`. The first
  entry is what the loaded woff2 in `apps/web/public/fonts/` actually
  satisfies; Berkeley Mono is the design intent, so the token name
  follows it.
- **Update** every in-file `var(--font-jetbrains-mono)` reference in
  `apps/web/src/styles.css` to `var(--font-berkeley-mono)` so no
  stale reference remains.
- **Remove** `/variables.css` from the repo root once `tokens.css`
  exists inside the app package.
- **Update** `docs/token-source.md`: drop the references to
  `DESIGN.md` and `tokens.json` (no longer exist), drop the
  `variables.css` mention (relocated), and rewrite the file's
  "source of truth" description to point at the new layout.
- **Hard rule** in the new capability: any `:root { ... }`
  declaration outside `apps/web/src/styles/tokens.css` is
  non-conforming. CI enforcement of the rule is intentionally a
  separate follow-up change.

## Capabilities

### New Capabilities

- `design-system`: owns the design-token catalog, component
  contracts, and motion vocabulary; establishes that any change
  to a token name, value, role, or component contract must flow
  through an OpenSpec change proposal.

### Modified Capabilities

None. This change adds a new capability only. Existing capabilities
(`web-frontend-app`, `detail-page-typography-consistency`,
`web-rebalance-frequency-display`) are not modified in this change.
A future change may collapse repeated visual-rule text in those
specs to references into `design-system`; it is intentionally out
of scope here.

## Impact

- Affected code:
  - `apps/web/src/styles.css`: drop `:root { ... }`, add
    `@import "./tokens.css"`, rename 5 `var(--font-jetbrains-mono)`
    references.
  - new file: `apps/web/src/styles/tokens.css`.
  - deleted file: `/variables.css`.
  - edited file: `docs/token-source.md`.
- Affected specs:
  - new: `openspec/specs/design-system/spec.md`.
- Validation:
  - `openspec validate add-design-system-spec` passes.
  - `openspec validate design-system` passes (after archive, the
    final spec must validate too).
  - `npm --prefix apps/web run typecheck` passes.
  - `npm --prefix apps/web run lint` passes.
  - `npm --prefix apps/web run test` passes.
  - `npm --prefix apps/web run build` passes.
  - Dev-server smoke: load `/` (Dashboard), `/signals/:id`,
    `/backtests/:id`; confirm the acid-lime primary button
    renders, the focus ring (`--focus-ring-color`) renders on
    Tab, and the monospace text actually uses the JetBrains Mono
    woff2 served from `/fonts/`.
- No `.tsx` / `.ts` edits, no API, no backend, no test fixture
  changes are expected.
