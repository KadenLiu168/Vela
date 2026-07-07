## Context

The `design-system` capability (`openspec/specs/design-system/spec.md`)
already locks `apps/web/src/styles/tokens.css` as the single canonical
token source. The existing token catalog is functional but inherits
three structural gaps and one typographic miss:

1. **Spacing scale is not stated as an 8px grid.** The primitives
   `4 / 8 / 12 / 16 / 20 / 24 / 28 / 32 / 36 / 40 / 48 / 56 / 60 / 64 /
   80 / 96 / 128 / 140` mix 4-multiples and 8-multiples. There is no
   semantic ladder for layout gaps (no `--space-*` aliases). Two
   declared primitives (`--spacing-28`, `--spacing-140`) are never
   consumed in `styles.css`.
2. **Type scale is missing common sizes.** `12` exists (`--text-label`)
   but `14`, `16`, `17` do not. `--text-body` is `15px` and
   `--leading-body` is `1.6`, while the design intent (F-102) is
   `16px / 1.5`. The dead aliases `--text-body-sm / --leading-body-sm
   / --tracking-body-sm / --text-body-lg / --leading-body-lg /
   --tracking-body-lg` exist in `tokens.css` but no `var(...)` site
   references them.
3. **Inter Variable OpenType features are inactive.** Inter Variable is
   declared as `--font-inter-variable` and a `@font-face` rule loads the
   variable woff2, but no `font-feature-settings` is set anywhere. The
   library ships single-storey `a` (`cv01`), curved `f` (`ss03`),
   slashed zero (`zero`), and contextual alternates (`calt`) — all
   inactive today.
4. **Card surfaces have no token family.** `.panel-primary`,
   `.dashboard-card`, `.metric-card`, and friends hand-roll
   `padding`, `background`, `border`, `border-radius`, and `box-shadow`
   from primitives at every selector.

The constraint is unchanged: `tokens.css` is the only place these
properties may be declared, and the gating rule
("Token and component changes flow through OpenSpec") already
guarantees that this change has a delta spec.

## Goals / Non-Goals

**Goals**

- Establish the 8px-grid spacing ladder as a first-class
  semantic alias family (`--space-*`) that future component changes
  consume instead of re-deriving spacing values from primitives.
- Complete the type scale with `14`, `16`, `17` so that any
  consumer can pick a named size without inventing a new one.
- Make body text render at the design-intended `16 / 1.5`
  (currently `15 / 1.6`).
- Activate Inter Variable OT features globally so default text
  uses single-storey `a`, curved `f`, slashed zero, and
  contextual alternates.
- Introduce a `--card-*` family that future component-polish
  changes can wire into card selectors without touching
  `tokens.css` again.

**Non-Goals**

- Migrating existing `var(--spacing-N)` call sites in
  `styles.css` to the new `--space-*` ladder. Consumers of
  `4 / 8 / 12 / 16 / 20 / 24 / 32 / 36 / 40 / 48 / 56 / 60 / 64 / 80 / 96 / 128`
  all keep resolving; only the unused `--spacing-28` and
  `--spacing-140` are removed.
- Migrating existing card selectors (`.panel-primary`,
  `.dashboard-card`, `.metric-card`, etc.) to consume
  `--card-*` tokens. That is the `design-system-component-polish`
  change (T2.2).
- Pruning the declared-but-unused `--text-body-sm / --leading-body-sm /
  --tracking-body-sm / --text-body-lg / --leading-body-lg /
  --tracking-body-lg`. The new ladder documents the intent; cleanup is
  cheap to do later but is not in scope here.
- Any change to monospace font (`--font-berkeley-mono`) — already
  governed by a separate Requirement.
- Adding Style Dictionary (`F-301`), Storybook (`F-304`), or a
  Stylelint guard — those are T2.4.

## Decisions

### D1. Spacing ladder uses semantic aliases on top of primitives, not a replacement

Keep every `--spacing-N` primitive that `styles.css` actually
consumes; add a `--space-*` ladder as aliases onto 8px multiples.

```
--space-xs:  var(--spacing-8);   /*  8 */
--space-sm:  var(--spacing-16);  /* 16 */
--space-md:  var(--spacing-24);  /* 24 */
--space-lg:  var(--spacing-32);  /* 32 */
--space-xl:  var(--spacing-48);  /* 48 */
--space-2xl: var(--spacing-64);  /* 64 */
--space-3xl: var(--spacing-96);  /* 96 */
```

**Rationale.** A pure "kill the primitives, only `--space-*` lives"
rewrite would force every existing `var(--spacing-12)` etc. call site
to migrate in the same change. The token foundations pass is the
wrong place to do that mass migration — that is what
`design-system-component-polish` is for. Aliases give new code the
8px-grid semantic and keep existing code untouched.

**Alternatives considered.**

- *Prune odd-multiples (`12`, `20`, `36`, `60`) and round consumers to
  8-multiples.* Rejected: forces dozens of unrelated `styles.css`
  edits into this change and risks subtle visual regressions that
  need a separate review pass per selector.
- *Add the ladder without pruning `--spacing-28` / `--spacing-140`.*
  Rejected: those two are dead weight, and pruning them is
  verifiably safe (no `var(--spacing-28)` or `var(--spacing-140)`
  sites in the repo, verified by `grep`).

### D2. New type sizes are added as new tokens; existing size tokens keep their values

Add `--text-14 / --text-16 / --text-17` plus `--leading-14 / --leading-16 / --leading-17`
(`1.5`). Migrate only `--text-body` (`15px → 16px`) and
`--leading-body` (`1.6 → 1.5`). Keep `--text-caption (13)`,
`--text-micro (11)`, `--text-label (12)`, `--text-subheading (24)`,
`--text-heading-sm (32)`, `--text-heading (48)`, `--text-heading-lg (64)`,
`--text-display (72)` unchanged.

**Rationale.** The new ladder is additive; the existing
`--text-body` value migrates to the design-intended 16 because that
is the explicit F-102 ask and the impact is limited (4 call sites
in `styles.css`).

**Alternatives considered.**

- *Rename `--text-body` to `--text-16` and migrate the 4 call sites.*
  Rejected: stricter than necessary. The token keeps the same name;
  consumers do not change; the value updates in one place.
- *Migrate body to 16 by adding a `--text-body: 16px` override and
  deleting the old value.* Equivalent to the chosen approach.

### D3. Inter Variable features are a single body-level rule, not a per-component opt-in

Add `--font-feature-settings-default: "cv01", "ss03", "zero", "calt";`
to `tokens.css` and apply via:

```css
body {
  font-feature-settings: var(--font-feature-settings-default);
}
```

**Rationale.** The four features are typographic defaults — every
piece of default text should look the same. Opt-in per component
would scatter the same four features across the codebase.

**Alternatives considered.**

- *Apply at `:root`.* Equivalent for this case but `body` makes the
  intent explicit (only default text gets the features; form
  inputs intentionally inherit their own platform settings).
- *Spread features across multiple tokens (`--font-feature-cv01`,
  `--font-feature-ss03`, ...).* Rejected: over-granular; the
  product never tunes these individually.

### D4. Card tokens are declared with sensible defaults and named after their role

```
--card-bg:            var(--surface-obsidian);
--card-border-color:  rgba(255, 255, 255, 0.06);
--card-padding-x:     var(--spacing-24);
--card-padding-y:     var(--spacing-20);
--card-radius:        var(--radius-cards);
--card-shadow:        var(--shadow-subtle-3);
--card-gap:           var(--element-gap);
```

**Rationale.** Aliases onto existing primitives mean no new
visual identity is introduced — the tokens are organizational,
not visual. Consumer migration is a separate change.

**Alternatives considered.**

- *Bake concrete pixel values into `--card-*`.* Rejected: breaks
  the alias principle that all primitives are owned by
  `tokens.css` and `--card-*` is a layer on top.
- *Split into `--card-bg / --card-bg-elevated / --card-bg-sunken`.*
  Rejected: speculative; the product only has one card surface
  today.

### D5. Spec uses ADDED-only Requirements

All four changes are additive or value-update. None of the
existing nine Requirements in `design-system/spec.md` is being
modified. The delta therefore contains four `ADDED Requirements`
and zero `MODIFIED / REMOVED / RENAMED`.

**Rationale.** Keeping the change as pure additions makes the
archive-time merge into the canonical `openspec/specs/design-system/spec.md`
a straightforward append, and it minimizes the risk of a
whitespace-sensitive header-text mismatch failing `openspec validate`.

## Risks / Trade-offs

- **Body size 15 → 16 affects 4 sites globally.** → Mitigation: the
  sites are panel-primary / card text on Dashboard, Signal Detail,
  Backtest Detail. One eyeball pass during the apply-loop review
  catches any text that overflows a fixed-width control.
- **`cv01` flips `a` from double-storey to single-storey.** → Mitigation:
  this is the design intent (Linear uses Inter with `cv01` on by
  default). One screenshot review during apply catches anything that
  looks wrong, but the change is intended.
- **`zero` slashed zero may confuse users who paste a `0` into a
  numeric input next to a letter `O`.** → Mitigation: this is a
  design-system-wide decision already in the design intent; the
  intent is consistent display across the app. Documented in the
  spec scenario.
- **`--card-*` tokens are declared but unused at merge time.** →
  Mitigation: the delta spec documents their existence and
  resolution; T2.2 wires them up. The unused-token risk is
  acknowledged in `openspec validate` (it surfaces unused tokens
  with a warning, not an error).
- **Header-text whitespace mismatch on archive-time merge.** →
  Mitigation: only `ADDED Requirements` are used, so no existing
  header needs verbatim re-typing.
