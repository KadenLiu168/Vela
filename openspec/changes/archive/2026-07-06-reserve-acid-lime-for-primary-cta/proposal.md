## Why

The `design-system` capability's "Buttons follow a three-variant
contract" declares that no other button in the same view may use
the acid-lime fill — the lime fill is reserved for the single
primary CTA per view. Two concrete violations exist today:

1. **Navigation active state is acid-lime filled.** Currently
   `.app-nav-link[aria-current="page"]` paints the active nav item
   with `background: var(--color-acid-lime)` and inverted text.
   This is one of the strongest accent uses available, but it is
   *not* a primary CTA in any view — it's a "you are here" cue.
   It uses the same visual budget the reserved CTA needs.
2. **Three of the three Operations-panel buttons are acid-lime.**
   `.operation-list button` styles Fetch market data, Generate
   signal, and Bootstrap / Setup database & data all the same
   way — three lime buttons in one view.

Both will be addressed; the navigation change lands in this
change, and the Operations-panel fix lands as soon as the
`unify-buttons-into-three-variants` change is archived (because
the variant classNames set up by that change are the natural
place to mark the Bootstrap button as primary and the others as
secondary).

This change formalizes:

- The Dashboard's primary CTA is **Bootstrap / Setup database &
  data**. The web-frontend-app spec is updated to state this
  explicitly so a future contributor cannot silently re-classify it.
- The nav active state uses **paper text + 2px underline** in the
  acid-lime color, consuming far less visual budget than a filled
  pill while keeping the accent for the primary CTA.

## What Changes

- **Change** the `.app-nav-link[aria-current="page"]` rule in
  `apps/web/src/styles.css`: replace the lime-filled chip with
  - `color: var(--color-paper)`
  - `background: transparent`
  - `box-shadow: inset 0 -2px 0 0 var(--color-acid-lime)`
    (an inset underline effect using the lime accent at 2px)
- **Update** `apps/web/src/components/AppShell.tsx` if needed for
  a11y (a screen-reader announcement of the active page is
  already carried by `aria-current="page"` — no JSX change
  expected beyond confirming the attribute is preserved).
- **Verify** that `.app-nav-link[aria-current="page"]:hover`
  stays sensible after the rule change (paper text on a slight
  background hover is fine).

This change does **not** touch the Bootstrap-vs-others question
inside `.operation-list`; that work belongs to the dependent
`unify-buttons-into-three-variants` change (which is landing
first or in parallel — order noted in `design.md`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `design-system`: Adds an "Acid-lime reservation" requirement
  with one scenario.
- `web-frontend-app`: Modifies the existing
  "Bootstrap button uses primary visual variant" requirement to
  state the page-level CTA designation explicitly.

## Impact

- Affected code:
  - `apps/web/src/styles.css` (the nav-link active-state rule)
  - `apps/web/src/components/AppShell.tsx` (no JSX change
    expected, but confirm)
  - `docs/token-source.md` (small note that `.app-nav-link`
    active state now uses the new visual treatment; optional)
- Affected specs:
  - delta to `openspec/specs/design-system/spec.md`
  - delta to `openspec/specs/web-frontend-app/spec.md`
- Validation: `openspec validate`, lint, typecheck, test, build;
  plus a manual DevTools visual QA of `/`, `/signals/:id`,
  `/backtests/:id` to confirm the nav active state looks
  correct on each.
- No API, no backend, no test fixture changes.

## Out of scope

- The Bootstrap-primary decision **in code**. This change
  formalizes the decision in spec text and updates the nav
  visual; the actual `.operation-list button` rewrite is the
  `unify-buttons-into-three-variants` change's job.
- Other nav treatment changes (e.g. font-weight on active).
- Mobile nav treatment (F-205 in the parent Initiative).
