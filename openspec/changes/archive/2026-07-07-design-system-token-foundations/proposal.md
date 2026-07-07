## Why

The `design-system` capability declares the canonical token surface, but
four token-related Initiative issues remain open and they all touch the
same single file (`apps/web/src/styles/tokens.css`). They have been held
back as four separate changes because individually each is too small to
justify its own proposal–review–archive cycle; together they form a
coherent "token foundations" pass that future component work can build
on without re-touching `tokens.css` for token plumbing.

The four issues are:

- **F-101 Spacing scale reconcile to 8px grid** — the current ladder
  mixes values that are and are not multiples of 8 (`4`, `12`, `20`, `28`,
  `36`, `60`). Two declared primitives (`--spacing-28`, `--spacing-140`)
  are unused. The product intent ("8px grid") is not currently stated in
  the spec or reflected as a semantic ladder.
- **F-102 Complete the type scale (add 12 / 14 / 16 / 17; body → 16 / 1.5)**
  — the ladder is missing `14`, `16`, `17`; `--text-body` is `15px / 1.6`
  but the design intent is `16px / 1.5`. `--text-body-sm` (15) and
  `--text-body-lg` (20) are declared but unused.
- **F-302 Apply Inter Variable `cv01` / `ss03` / `zero` features globally**
  — Inter Variable is loaded but no `font-feature-settings` is declared,
  so single-storey `a`, curved `f`, and slashed zero (the typographic
  affordances Inter Variable ships with) are not active.
- **F-303 Unify Card component on shared `--card-*` tokens** — card
  surfaces in `styles.css` re-implement spacing, radius, and border
  primitives at the call site; there is no `--card-*` token family.

## What Changes

- **Spacing**: introduce an 8px-grid semantic ladder
  `--space-{xs,sm,md,lg,xl,2xl,3xl}` resolving to `8 / 16 / 24 / 32 / 48 / 64 / 96`.
  Prune the two declared-but-unused primitives (`--spacing-28`,
  `--spacing-140`). All `--spacing-N` primitives currently consumed by
  `styles.css` (`4 / 8 / 12 / 16 / 20 / 24 / 32 / 36 / 40 / 48 / 56 / 60 / 64 / 80 / 96 / 128`)
  remain — no consumer migration in this change.
- **Type**: add `--text-14`, `--text-16`, `--text-17` plus
  `--leading-14`, `--leading-16`, `--leading-17` (`1.5`).
  Migrate `--text-body` value from `15px` → `16px` and `--leading-body`
  value from `1.6` → `1.5`. The four `var(--text-body)` /
  `var(--leading-body)` consumers in `styles.css` automatically pick up
  the new values; no manual edit required.
- **Type cleanup** (optional, low risk): the declared-but-unused
  `--text-body-sm / --leading-body-sm / --tracking-body-sm /
  --text-body-lg / --leading-body-lg / --tracking-body-lg` are not
  pruned in this change to keep the scope tight; the new ladder
  documents the intent.
- **Inter Variable features**: declare
  `--font-feature-settings-default: "cv01", "ss03", "zero", "calt";`
  in `tokens.css` and apply it via `font-feature-settings: var(...)`
  on `body` in `styles.css`. This activates single-storey `a`, curved
  `f`, slashed zero, and contextual alternates for all default text
  without per-component opt-in.
- **Card tokens**: introduce a `--card-*` family in `tokens.css`:
  - `--card-bg: var(--surface-obsidian);`
  - `--card-border-color: rgba(255, 255, 255, 0.06);`
  - `--card-padding-x: var(--spacing-24);`
  - `--card-padding-y: var(--spacing-20);`
  - `--card-radius: var(--radius-cards);`
  - `--card-shadow: var(--shadow-subtle-3);`
  - `--card-gap: var(--element-gap);`
  No consumer migration in this change; the tokens are available for the
  follow-up `design-system-component-polish` change (T2.2) to wire them
  into actual `.panel-primary`, `.dashboard-card`, and similar selectors.
- **Spec**: extend `openspec/specs/design-system/spec.md` with three new
  Requirements covering (a) the 8px-grid spacing ladder, (b) the
  completed type scale with body at 16/1.5, and (c) Inter Variable
  OpenType features. Card tokens get a lightweight Requirement
  documenting their existence and resolution; enforcement that card
  surfaces consume them is deferred to T2.2.
- **Docs**: append the four issue IDs (F-101 / F-102 / F-302 / F-303)
  to the closing-notes of the existing `design-system` capability so the
  capability–issue mapping stays auditable.

No breaking semantic changes for any current consumer of
`apps/web/src/styles.css`:

- `var(--text-body)` still resolves (now to 16 px instead of 15 px).
- `var(--spacing-N)` for all N in actual use still resolves.
- `var(--leading-body)` still resolves (now to 1.5 instead of 1.6).
- All previously declared tokens remain.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `design-system`: adds Requirements for
  (a) the 8px-grid spacing ladder,
  (b) the completed type scale (12 / 13 / 14 / 16 / 17 / 20 / 24 / 32 / 48 / 64 / 72)
  with body at 16 / 1.5,
  (c) Inter Variable OpenType features (`cv01`, `ss03`, `zero`, `calt`)
  applied globally, and
  (d) the `--card-*` token family.
  The "Token and component changes flow through OpenSpec" requirement
  remains the gating contract for future additions.

## Impact

- **Files**:
  - `apps/web/src/styles/tokens.css` — additive (new tokens) + two
    primitive values updated (`--text-body`, `--leading-body`) + two
    unused primitives pruned (`--spacing-28`, `--spacing-140`).
  - `apps/web/src/styles.css` — one new selector rule
    (`body { font-feature-settings: ... }`); no other changes.
  - `openspec/specs/design-system/spec.md` — four new Requirements +
    three to six new Scenarios.
- **Consumers**: every `var(--text-body)` / `var(--leading-body)` site
  in `styles.css` (4 lines, all in card / panel primary text) gets
  `16px / 1.5` instead of `15px / 1.6`. This is the intended design
  outcome, but it is a visible change — flagged here so reviewers can
  eyeball one Dashboard / Signal Detail / Backtest Detail render after
  apply.
- **Risks**:
  - Body size shift 15 → 16 is global. Mitigated by the small number
    of consumers and the canonical Linear-style spacing they live in.
  - Inter Variable OT features activate `cv01` (single-storey `a`) and
    `zero` (slashed zero) across the entire app — this is the intended
    outcome but is a visual change worth one screenshot review.
  - Card tokens are declared but not yet wired. Their existence is a
    pure foundation step; no consumer is broken if they are unused.
