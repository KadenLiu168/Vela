## Context

The 2026-07-04 `migrate-web-to-linear-design-system` change rewrote
the Linear design system into `apps/web/src/styles.css`, but did not
establish a top-level ownership of "design tokens" inside OpenSpec.
The result, examined during the 2026-07-06 design review, was that
`apps/web/src/styles.css` declared its own `:root { ... }` block,
duplicating the catalog that `/variables.css` held, with **no file
importing `variables.css`**. Today's manual rename of
`--font-jetbrains-mono` → `--font-berkeley-mono` in `variables.css`
made the drift concrete: the runtime still resolves the old name
because styles.css declares the old name in its own `:root`, while
the catalog now lives under a different name. Two conflicting
token systems in the same repo.

Three stakeholders are affected:

- **Future contributors** who need to add or change a token and
  cannot easily find the canonical source.
- **OpenSpec reviewers** who have no top-level design-system
  capability to anchor visual rules against.
- **The web build** itself, which currently renders tokens from a
  silent on-the-side `:root` block instead of any catalog file.

The parent Initiative ("Align Vela Web with Design System +
Tokenize Implementation", issue F-305) lists this work as its
final P3 child issue with a 3-point estimate. This change is that
work.

## Goals / Non-Goals

**Goals:**

- Establish `apps/web/src/styles/tokens.css` as the single
  `:root { ... }` declaration site for the web frontend, and
  `apps/web/src/styles.css` as the only consumer of that catalog.
- Promote design-system into a top-level OpenSpec capability with
  three requirement groups (Tokens, Components, Motion) and a
  change-gate that makes future token additions routable through
  OpenSpec proposals.
- Close the half-applied F-002 font rename so
  `var(--font-berkeley-mono)` resolves at runtime to the loaded
  JetBrains Mono woff2.
- Make drift of the form "stylesheet declares a new
  `:root` block independently" structurally impossible from this
  PR onward.

**Non-Goals:**

- No Style Dictionary build pipeline. F-301 in the parent
  Initiative will own that when it lands; this change makes it
  possible, not necessary.
- No light/dark themes, no `data-theme` toggle, no per-page theme.
- No extraction of `tokens.css` into a shared package. The web
  frontend is the only consumer today.
- No rewriting of `web-frontend-app/spec.md`,
  `detail-page-typography-consistency/spec.md`, or
  `web-rebalance-frequency-display/spec.md` to point at the new
  capability. Their existing visual rules remain in place; future
  changes may collapse repeated text into references, but doing
  it here would couple unrelated scopes.
- No CI hook that mechanically fails a `:root` declaration
  outside `tokens.css`. The spec ships the rule; the enforcement
  is a follow-up change so we can choose the right tool
  (Stylelint, custom Vite plugin, or grep-based check) without
  blocking this PR.
- No changes to `.tsx` / `.ts` files, API, backend, or test
  fixtures.

## Decisions

### 1. Canonical token file lives at `apps/web/src/styles/tokens.css`

- **Alternative considered**: keep `variables.css` at the repo
  root and import it from `apps/web` via a Vite alias.
- **Why not**: a token file at the repo root is invisible to
  Vite's CSS pipeline (HMR, source maps, hashing,
  dead-code-elimination) without bespoke config. Putting it in
  the same package as its only consumer makes it canonical-by-
  location, and slots naturally into F-301's eventual output
  path.
- **Side effect**: `docs/token-source.md`, which names the
  current sources, must be rewritten to drop the `/variables.css`
  mention and the deleted `DESIGN.md` / `tokens.json` mentions.

### 2. `styles.css` imports `tokens.css` via a single `@import` line

- **Alternative considered**: import both in `main.tsx`
  (`import "./tokens.css"; import "./styles.css";`).
- **Why not**: keeping the CSS dependency graph inside the CSS
  (`@import "./styles/tokens.css";` at the top of `styles.css`)
  means consumers reading `styles.css` see cascade order
  immediately, and `main.tsx` stays at one line.
- **Resolution rule**: `@import` declarations MUST come before
  any rule. Vite hoists them at build time; at runtime the
  browser enforces this. The `:root` block in `tokens.css`
  therefore defines custom properties before any selector in
  `styles.css` consumes them.

### 3. Monospace token stays under the Linear design name, with a
JetBrains-first value chain

- **Alternative considered**: rename the token to
  `--font-jetbrains-mono` so the name matches what loads.
- **Why not**: that devolves the spec away from the design
  source. The Linear reference names this token
  `--font-berkeley-mono`; a `JetBrains Mono` fallback belongs
  in the value chain, not the name. The current
  `apps/web/src/styles.css` `@font-face` rule declares
  `font-family: "JetBrains Mono"`, which the browser will match
  against the first entry of the chain
  (`'JetBrains Mono', 'Berkeley Mono', ui-monospace, …`).

### 4. Implementation-only tokens fold into `tokens.css` instead of
becoming a parallel `:root`

- **Alternative considered**: keep `--text-body`,
  `--feedback-accent-*`, `--radius-cards`, etc. inside
  `apps/web/src/styles.css :root`, and only require the Linear
  primitive tokens in `tokens.css`.
- **Why not**: that preserves two `:root` blocks and re-creates
  the same drift surface, just smaller. The goal is *one*
  declaration site for the entire web frontend.

### 5. One OpenSpec capability, one `spec.md`, three requirement groups

- **Alternative considered**: three capabilities
  (`design-system-tokens`, `design-system-components`,
  `design-system-motion`), each with its own `spec.md`.
- **Why not**: the OpenSpec CLI validates one
  `specs/<capability>/spec.md` per capability. Splitting into
  three capabilities triples the validation surface and the
  archive ceremony for a body of rules that conceptually belong
  together. Inside a single `spec.md`, three sections
  (`### Requirement: Tokens`, `### Requirement: Components`,
  `### Requirement: Motion`) carry the same separation without
  the overhead.

## Risks / Trade-offs

- **`@import` cascade order** → assume correctness for the
  declarations being moved; any `@font-face` already in
  `styles.css` stays there (fonts must be declared in the
  stylesheet that consumes their custom properties). Verified
  by `npm --prefix apps/web run build` and the dev-server smoke
  test.
- **`var(--font-berkeley-mono)` references in the 5 consumer
  sites could miss a manual case** → mitigation: search the
  whole `apps/web/src/` tree for `var(--font-jetbrains-mono)`
  *before* merging; merge only on zero hits. The compile + visual
  QA pass is the second line of defense.
- **The hard rule ("no `:root` outside `tokens.css`") has no
  automated enforcer in this PR** → mitigation: the spec calls
  the rule out explicitly, and the proposed follow-up change is
  a single small PR (Stylelint rule or Vite plugin) — a few
  days, not weeks.
- **`/variables.css` lives at the repo root while the canonical
  file moves into the app** → mitigation: the migration PR
  deletes `/variables.css` in the same commit as it creates
  `apps/web/src/styles/tokens.css`. There is no intermediate
  state where both exist.
- **`docs/token-source.md` becomes out of date again if someone
  adds a new design doc** → out of scope to enforce in this
  PR; future rule may move into `design-system` itself.

## Migration Plan

Single PR with the following commit order inside it:

1. **prep**: complete the half-applied font rename in
   `variables.css` (the value chain `'JetBrains Mono', 'Berkeley
   Mono', ...`) — non-functional but makes the file consistent
   for the diff reviewer.
2. **catalog**: create `apps/web/src/styles/tokens.css` with
   the contents of `/variables.css`, the implementation-only
   tokens added, and the new font chain.
3. **wire**: delete the `:root` block from
   `apps/web/src/styles.css`; prepend `@import "./styles/tokens.css";`
   to `styles.css`.
4. **rename**: change every `var(--font-jetbrains-mono)` to
   `var(--font-berkeley-mono)` in `styles.css`.
5. **cleanup**: delete `/variables.css`; rewrite
   `docs/token-source.md`.
6. **spec archive**: run `openspec-archive-change
   add-design-system-spec` so the proposal + delta spec folds
   into `openspec/specs/design-system/spec.md`.

**Rollback**: revert the PR. No data migration, no schema
change; the worst case is a one-PR revert.

## Open Questions

- **CI enforcement**: which tool — Stylelint with a custom
  declaration-property-value rule, a Vite plugin that scans at
  build time, or a grep-based `npm` script run in CI? To be
  decided in the follow-up change.
- **`@font-face` placement**: today the rules live at the top of
  `apps/web/src/styles.css`. Should the future follow-up move
  them into `apps/web/src/styles/fonts.css` for symmetry with
  the tokens split? Out of scope here.
- **Document the design system externally?** The
  `docs/architecture.md` does not currently mention design
  tokens. A short paragraph there may be warranted, but is
  intentionally outside the scope of this change.
