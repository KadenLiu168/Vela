## Why

The `design-system` capability (archived `add-design-system-spec`
spec, requirement "Buttons follow a three-variant contract") already
mandates that every button in the web frontend be one of exactly
three variants: `primary` (filled accent), `secondary` (outline /
ghost), or `tertiary` (text-only). No fourth treatment is permitted
without a new OpenSpec change.

The web app's codebase today does not consume these variants as a
contract — instead, three separate button className
families exist:

- `.operation-list button` (CSS selector targeting any `<button>`
  in the Operations panel) — currently applies the acid-lime
  primary style indiscriminately to **three distinct operations**
  in the same view, which is itself a violation of the
  per-view-primary-CTA reservation rule (to be fixed by the
  separate `reserve-acid-lime-for-primary-cta` change).
- `.bootstrap-action` — a className already used in the JSX layer
  for the Bootstrap button, but **with no CSS rule** of its own; it
  currently rides on `.operation-list button`.
- `.dashboard-refresh-action` — a one-off button class with its own
  outline treatment.

This change brings the code into conformance with the existing
`design-system` requirement: every `<button>` in `apps/web/src/`
gets a className from a small, documented set mapping 1-to-1 to the
three spec variants, and CSS rules consume those classes (no
descendant-selector leakage across variants).

## What Changes

- **Refactor** every `<button>` in `apps/web/src/` to one of three
  variant classes: `.button-primary`, `.button-secondary`, or
  `.button-tertiary`.
- **Replace** the descendant-selector leakage: `.operation-list
  button` and any other selector that styles buttons by ancestry
  disappears. CSS now targets the variant class directly.
- **Keep** the existing semantic className (`bootstrap-action`,
  `dashboard-refresh-action`, `signal-empty-action`,
  `operation-list`) on each button as the "what role does this
  button play" hint, alongside the variant class. The variant class
  is what carries visual treatment; the semantic class carries
  context (used by tests, accessibility names, future Storybook
  catalog).
- **Add** per-variant CSS rules reading the design tokens
  already declared in `tokens.css`.
- **Drop** the dead `.bootstrap-action` CSS gap (it had no rule;
  now it shares `.button-primary`'s lime fill).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The existing `design-system` requirement "Buttons follow a
three-variant contract" already declares the rule this change
implements. No requirement text is being changed; the change is
"code follows spec."

(Rationale for omitting spec delta: adding a clarifying scenario
about variant classes was considered but rejected; the existing
scenarios already pin the visual contract precisely enough. The
follow-up `reserve-acid-lime-for-primary-cta` change adds a
reservation rule that this change inherits.)

## Impact

- Affected code:
  - `apps/web/src/styles.css` (add 3 variant rules; remove
    `.operation-list button` selector; reconcile
    `.dashboard-refresh-action`, `.signal-empty-action`,
    `bootstrap-action`)
  - `apps/web/src/pages/DashboardPage.tsx` (variant classes on
    5 buttons; remove `.dashboard-refresh-action` from the button
    itself, keep as aria/class for semantics)
  - `apps/web/src/components/FeedbackMessage.tsx` (if it
    contains buttons — verify)
  - `apps/web/src/components/FirstRunGuidance.tsx` (if any
    button — verify)
- Affected specs: none.
- Validation: existing frontend typecheck, lint, test, build;
  visual QA against the existing screenshot of the Dashboard
  Operations panel (Bootstrap stays acid-lime; the other two
  operations move to outline); plus the upcoming
  `reserve-acid-lime-for-primary-cta` change should compose cleanly
  on top.
- No API, no backend, no test fixture changes expected.

## Out of scope

- Visual rebranding of any button besides the three
  `.operation-list` buttons. Dashboard heading refresh button,
  empty-state buttons, feedback-message actions stay where they are
  stylistically; they just become explicit variants instead of
  riding selector inheritance.
- Tooltip / icon-button variants.
- Storybook/Ladle catalog (this is F-304 in the parent Initiative).
- Per-view primary CTA reservation — that is a separate change
  (`reserve-acid-lime-for-primary-cta`) which depends on this
  change landing first.
