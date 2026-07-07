## Context

The `design-system` capability (archived `add-design-system-spec`)
already declares that buttons are one of exactly three variants.
The web app's code currently uses three different selector
mechanisms (`.operation-list button`, `.bootstrap-action` no-op,
`.dashboard-refresh-action`) that bypass the contract. This change
brings the code into conformance without modifying the spec.

The cleanest implementation is a new className family with one
class per variant, dropped into CSS alongside the existing
token-based typography / color / radius rules. The descendant
selector `.operation-list button` disappears in the same commit so
that no rule can "leak" lime to a non-primary button.

## Decisions

1. **Variant class is canonical, semantic className is contextual.**
   - Each `<button>` carries two classNames:
     - `button-{variant}` for visual treatment (CSS rules).
     - The original semantic className (`bootstrap-action`,
       `dashboard-refresh-action`, etc.) for accessibility,
       testing, and any future Storybook catalog.
   - Rationale: keeping the semantic class as a hint preserves
     test selectors, ARIA-like data-attrs, and downstream
     cataloging. It costs zero CSS.

2. **CSS targets the variant class directly. No `.foo button`.**
   - Alternative: keep descendant selectors and just add
     `button-secondary` as a second class.
   - Rationale: descendant selectors are how we got here — three
     `button` rules in one panel selecting "anything I happen to
     be nested in" is exactly the drift the Initiative is fixing.
     Removing the descendant selector means the next refactor can't
     accidentally re-introduce the same bug.

3. **`.button-primary` is the only lime fill.**
   - All other buttons (`.button-secondary`, `.button-tertiary`)
     use neutral treatment.
   - This rule enforces the per-view-primary-CTA reservation that
     `reserve-acid-lime-for-primary-cta` will codify at the spec
     layer.

4. **No spec delta needed.**
   - The existing `design-system` requirement "Buttons follow a
     three-variant contract" already pins the rule precisely
     enough. Adding a new scenario here would be redundant.

## Risks / Trade-offs

- **Test breakage**: existing tests may select buttons by their
  semantic className (e.g. `.bootstrap-action`) and could now
  also match `.button-primary` accidentally. → Mitigation:
  pre-merge, run the full vitest suite; if any test relies on a
  *visible* property, update it to select by the variant class
  instead.
- **Empty-action button styling**: `EmptyAction` is a small
  component; if it doesn't already carry a className, the change
  has to add one (`.button-secondary`) at the call site or inside
  the component. → Mitigation: read the component file early in
  implementation; if `EmptyAction` reuses the secondary look,
  apply the class inside the component.
- **Hover/focus state regression**: removing
  `.operation-list button` may also remove previously-defined
  `:hover`/`:focus` rules for that selector. → Mitigation:
  port those pseudo-class rules verbatim onto the new variant
  classes.

## Migration Plan

Single PR. Steps inside:

1. Add three variant rules in `apps/web/src/styles.css` (replacing
   `.operation-list button` body):
   ```css
   .button-primary {
     background: var(--color-acid-lime);
     color: var(--color-void);
     border: 1px solid var(--color-acid-lime);
     /* typography, padding, radius, transition, focus ring … */
   }
   .button-secondary { /* outline / ghost */ }
   .button-tertiary  { /* text-only */ }
   ```
2. Refactor classNames in `DashboardPage.tsx`:
   - `Bootstrap` button → `className="bootstrap-action button-primary"`
   - `Fetch market data`, `Generate signal` → `className="button-secondary"`
   - `Refresh Dashboard` (heading refresh) → drop
     `dashboard-refresh-action` rule, attach `button-secondary`
   - `EmptyAction` instances → attach `button-secondary` either at
     the component or at call sites
3. Verify `FeedbackMessage.tsx`, `FirstRunGuidance.tsx`,
   `BacktestRunForm.tsx` for hidden buttons; refactor where found.
4. Run validation suite.
5. Archive.
