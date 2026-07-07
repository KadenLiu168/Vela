## Context

T2.1 `design-system-token-foundations` shipped nine new token families
and four new requirements; it deliberately did not migrate any
existing consumers. T2.2 is the consumption pass for five Initiative
issues that were stranded waiting on those tokens:

- F-103 (nav radius), F-106 (status pills), F-201 (dashboard ladder),
  F-2.2 (line-height magic values), F-3A.9 (`EmptyAction` variant).

Three of these five (F-106, F-2.2, the radius-mapping portion of
F-103) are pure code-conformance with rules that already exist in the
`design-system` capability. The other two (F-201, F-3A.9) add new
contract surface and therefore need new spec Requirements.

The constraint is unchanged: this change lives at the CSS + a single
React component (`EmptyAction`), and modifies only files that are
already owned by the `design-system` and `web-frontend-app` capabilities.

## Goals / Non-Goals

**Goals**

- Bring existing CSS into conformance with the `design-system`
  rules already shipped in T1 / T2.1:
  - `.app-nav-link` stops using the capsule radius.
  - Four `.status-pill-*` selectors use `--feedback-accent-*`.
  - Two `line-height: <magic>` declarations use `--leading-*`.
- Add two new spec Requirements that pin the cross-cutting
  decisions made by this change (radius mapping + dashboard ladder).
- Make the `EmptyAction` helper reusable from non-secondary-CTA
  call sites by accepting a `variant` prop.

**Non-Goals**

- Migrating card selectors (`.panel-primary`, `.dashboard-card`,
  `.metric-card`, etc.) to consume the new `--card-*` family.
  That is a separate change after T2.2 (the `EmptyAction` change
  is the only React component touched here).
- Replacing other raw `--color-*` palette usages outside the four
  status pills. The remaining raw usages are intentional non-fill
  lime (focus rings, hover underlines, SVG strokes) per the
  acid-lime reservation rule and are out of scope.
- Migrating every `--spacing-N` call site in `styles.css` to the
  new `--space-*` ladder. That is a separate, larger change
  after T2.2.
- Introducing a real `<Pill>` or `<Badge>` component. The
  `--radius-pills` token remains available; this change only
  removes the nav from that family.
- Stylelint enforcement (the `F-3A.7 / F-3B.4` follow-up from T1).
  Belongs to T2.4.

## Decisions

### D1. Nav loses its capsule; mapping is `radius-md` (6 px)

Change `.app-nav-link { border-radius: var(--radius-pills); }` to
`border-radius: var(--radius-md)`.

**Rationale.** `--radius-md` (6 px) produces a "soft tile" that
matches the Linear / Vela visual language for nav items and
buttons. `--radius-sm` (2 px) is too sharp for a top-level
chrome element; `--radius-buttons` is intentionally the same as
`--radius-md` for nav so the visual language stays unified. The
`--radius-pills` token remains available for true badge / tag
components in a future change.

**Alternatives considered.**

- *Keep the capsule, document it.* Rejected: the Initiative
  explicitly says "remove capsule shape from nav". The visual
  intent is the whole point of F-103.
- *Use `--radius-sm` (2 px).* Rejected: too sharp for a top-level
  nav. Would have made the nav look like an old Windows control.

### D2. Status pill neutral darkens; that is the spec

The four pill migrations are pure spec conformance with the
"feedback accents resolve to the named palette tokens" rule.
The neutral pill darkens from `#62666d` (`--color-ash`) to
`#383b3f` (`--color-smoke`, via `--feedback-accent-empty`).

**Rationale.** The existing spec already documents that empty /
muted state should use `--feedback-accent-empty`. The pill family
is exactly that signal: "no status, pending, skipped, neutral".
Darker neutral reads as "muted by intent" rather than "almost
success".

**Alternatives considered.**

- *Keep `--color-ash` for neutral, only migrate the other three.*
  Rejected: that leaves the family non-conforming with the spec;
  future lint will flag it. Better to fix once and document the
  visual shift in the commit body.
- *Override `--feedback-accent-empty` to resolve to `--color-ash`
  in this change.* Rejected: that's a token semantics change for
  the whole product. Belongs to a separate decision if the user
  ever wants the lighter neutral.

### D3. Dashboard ladder is discrete, not fluid

Replace `font-size: clamp(var(--text-heading), 6vw, var(--text-display))`
on `.dashboard-heading h1` with a discrete 3-step ladder:
48 / 64 / 72 px at default / 768 px / 1280 px.

**Rationale.** "Responsive ladder" in the Initiative title means
discrete steps, not fluid ramp. The current fluid clamp misses the
64 px rung entirely (it interpolates 48 → 72 directly, hitting
64 only as a transient in-between value). The discrete ladder
produces the canonical three sizes exactly.

**Alternatives considered.**

- *Keep the fluid clamp and document it as the ladder.* Rejected:
  the Initiative explicitly names 48 / 64 / 72 as the ladder; fluid
  ramp does not produce 64 as a stable size.
- *Use 4 or 5 breakpoints (e.g. add 1024 px rung).* Rejected: out
  of scope; spec pins 3 steps; future change can add steps.

### D4. `--leading-snug` is a new token at 1.4

Add `--leading-snug: 1.4;` to `tokens.css` for the one
`.workflow-grid strong, .detail-page dd` site.

**Rationale.** 1.4 is between `--leading-body` (1.5) and
`--leading-body-lg` (1.33); semantically it is "snug" — tighter
than body but looser than a subheading. Adding the token is the
cheapest way to bring the one remaining magic value into
conformance without rounding it to 1.5 or 1.33.

**Alternatives considered.**

- *Round to `--leading-body` (1.5).* Rejected: 0.1 line-height is
  a visible density change for emphasized text inside a
  workflow-grid / detail-page definition list; spec preserves the
  design intent.
- *Round to `--leading-body-lg` (1.33).* Rejected: similar density
  change in the other direction.

### D5. `EmptyAction` gains a `variant` prop, stays inline

Extend the inline `EmptyAction` function signature with a
`variant` prop (string union `"button-primary" | "button-secondary"
| "button-tertiary"`, default `"button-secondary"`). Render
`` <button className={variant} ...> ``. The two existing call
sites keep the default. No extraction to a new file.

**Rationale.** The variant prop is the smallest change that
makes the component reusable for non-secondary empty states
(e.g. "Generate signal" could one day want a primary CTA). Keeping
the function inline matches the rest of `DashboardPage.tsx`'s
helper pattern (`OperationPendingFeedback`, `OperationErrorSummary`,
etc.). A future extraction to `apps/web/src/components/EmptyAction.tsx`
is a one-line move once a second consumer needs it.

**Alternatives considered.**

- *Extract to a new file `EmptyAction.tsx` now.* Rejected: only
  one consumer; new file adds zero review value this iteration.
- *Default to `button-primary` instead of `button-secondary`.*
  Rejected: the existing call sites all use secondary and the
  primary variant is reserved for the per-view primary CTA
  (Bootstrap on Dashboard). Defaulting to secondary preserves
  behavior at all current call sites.

### D6. Spec is mostly ADDED-only; F-106 / F-2.2 are pure code conformance

The delta spec adds two new Requirements to `design-system`
(radius mapping, dashboard ladder) and one new Requirement to
`web-frontend-app` (`EmptyAction` variant-aware). F-106 and F-2.2
do not need new Requirements because the rules they enforce
already exist (the feedback-accent rule and the line-height-token
rule, both added in T1).

**Rationale.** The whole point of F-106 and F-2.2 is to bring
existing code into conformance with rules that are already in
place. Adding *new* Requirements for "this code now conforms"
would be paperwork noise.

**Alternatives considered.**

- *Add "F-106 / F-2.2 conformance" Requirements anyway.* Rejected:
  duplicates existing Requirements; archive merge would either
  produce redundant text or fail the "no duplicate Requirement
  names" check.

## Risks / Trade-offs

- **Nav visual change** (capsule → tile) is irreversible via spec
  rule. → Mitigation: review on Dashboard / Signal Detail /
  Backtest Detail in dev server before archive; reject-and-revise
  if reviewers object.
- **Neutral pill darkens** (visual). → Mitigation: documented in
  commit body; the change is the spec-conformant choice.
- **Dashboard heading goes from fluid to discrete**; intermediate
  widths (768–1280 px) are now locked at 64 px. → Mitigation:
  spec pins the breakpoints; documented in commit body.
- **EmptyAction API adds a prop** — call sites unchanged today
  but future callers must import the type. → Mitigation: the
  variant prop has a default; behavior at current call sites is
  identical.
- **Header-text whitespace mismatch on archive-time merge** →
  Mitigation: spec uses only ADDED Requirements, all with new
  unique names, so no existing header needs verbatim re-typing.
