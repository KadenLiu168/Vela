## Context

The Initiative's design review (F-104 child issue) flagged two
violations of the per-view-primary-CTA reservation rule:

1. The nav active state uses the lime fill — a much louder visual
   than the rule reserves for "you are here."
2. Three Operations-panel buttons all get `.operation-list button`
   styling — three limes in one view.

The user (frontend lead) decided to:

- Keep the lime accent reserved for the **single primary CTA per
  view**.
- Pick **Bootstrap / Setup database & data** as that primary in
  the Dashboard.
- Repaint the nav active state with **paper text + 2px lime
  underline**.

This change lands the visual treatment of the nav; the Operations-
panel CTAs are not yet refactored here — that needs
`.button-primary` / `.button-secondary` classNames from the
`unify-buttons-into-three-variants` change. Sequencing is in
[Risks / Migration Plan](#risks--trade-offs).

## Decisions

1. **`box-shadow: inset 0 -2px 0 0 var(--color-acid-lime)` over
   `border-bottom`.
   - Alternative: `border-bottom: 2px solid var(--color-acid-lime)`.
   - Rationale: border-bottom changes layout (`box-sizing`
     differences, 2px height bump). Inset box-shadow is decoration
     only — `box-sizing: border-box` plus this rule doesn't shift
     the box by 2px; the underline hugs the bottom edge of the
     existing box, similar to how Linear's marketing nav works.

2. **Hover state reduces accent but doesn't kill it.**
   - `.app-nav-link[aria-current="page"]:hover` was
     `background: var(--color-bone); color: var(--color-void);`
     — a chip-flip back to neutral. With the new transparent
     background, hover swap is just slight text/opacity change
     (paper → bone, or paper with 0.88 opacity).
   - Decision: change hover to `color: var(--color-bone)`; keep
     underline.

3. **Reservation rule goes into design-system, not web-frontend.**
   - The rule itself is a design rule, not a frontend app rule.
   - Web-frontend gets one explicit MODIFIED scenario stating that
     Dashboard's primary CTA is Bootstrap.

4. **`Bootstrap` is the only primary CTA across `/`,
   `/signals/:id`, `/backtests/:id`.
   - User explicitly answered this question in the planning
     discussion; no product input is needed before merge.
   - The other two Operations buttons (Fetch market data, Generate
     signal) become secondary (`.button-secondary`). That work
     follows in `unify-buttons-into-three-variants`.

## Risks / Trade-offs

- **Sequencing risk**: this change ships the visual treatment of
  the nav and the spec rule; the actual `.button-primary` /
  `.button-secondary` className refactor of the Operations panel
  depends on `unify-buttons-into-three-variants`. → Mitigation:
  either land this first (cleaner spec git history), or land them
  in sequence with this change archived **before** that one so the
  reservation rule is already codified when the variant refactor
  lands. The opening-sentence of [Migration Plan](#migration-plan)
  pins the order.

- **Nav-link default state**: unchanged, so users see no surprise
  on inactive items.

- **Paper vs bone text**: keeping paper (not bone) on the active
  underline keeps the "you are here" item as the strongest text
  presence in the nav bar, which is correct a11y.

## Migration Plan

Single PR, sequenced FIRST before `unify-buttons-into-three-variants`
so the reservation rule is in place when that refactor lands.

1. Replace the active-state rule body in `apps/web/src/styles.css`.
2. Run `openspec validate`, lint, typecheck, test, build.
3. Archive this change.
4. (Out of scope of this PR) `unify-buttons-into-three-variants`
   will then refactor `.operation-list button` so Bootstrap becomes
   `.button-primary` and the other two become `.button-secondary`,
   which is what makes the reservation rule visually honest.
