## Context

The web frontend now ships a complete design-system surface:
canonical tokens (T2.1), three-variant buttons (T1), radius
mapping (T2.2), feedback-accent rules (T1 + T2.2), a discrete
dashboard ladder (T2.2), and a state-component set (T2.3). Every
one of those rules lives in the `design-system` capability and is
enforced only by human code review at PR time. None of it is
machine-checked.

Three Initiative issues remain that close that gap:

- **F-3A.7 Stylelint guard** — encodes the design-system
  invariants as CSS lint rules so violations fail in CI, not
  at code review.
- **F-304 Storybook / Ladle component catalog** — gives
  developers (and the user, and QA) a visual surface to see
  every component with every variant and every control.
- **F-301 Style Dictionary / token tooling** — the original
  ask was "auto-sync tokens.json → CSS variables". That ask
  is obsolete: F-305 deleted `tokens.json` and made
  `tokens.css` the canonical source. The remaining value of
  F-301 is *discoverability* — a generated Markdown token
  reference that documents what tokens exist and what they
  resolve to. We achieve this with a small Node script, no
  new dependency.

The constraint surface is unchanged: this change touches the
web app's build / lint / dev tooling, and adds to
`openspec/specs/design-system/spec.md`. It does not change any
runtime behavior of the web frontend.

## Goals / Non-Goals

**Goals**

- Add Stylelint with five rule categories that encode the
  design-system invariants already shipped (button variant,
  line-height tokens, radius tokens, `:root` placement,
  acid-lime reservation).
- Add Ladle component catalog with stories for each state
  component (FeedbackMessage, Skeleton, ErrorBoundary,
  EmptyState).
- Generate `docs/tokens.md` from `tokens.css` so the token
  catalog is discoverable.
- Add three new Requirements to the `design-system` capability
  pinning each of the above.

**Non-Goals**

- **Replacing tokens.css with a JSON-based token source.**
  F-301's original ask ("Style Dictionary to auto-sync
  `tokens.json`") is no longer applicable. We are not
  re-introducing `tokens.json`.
- **Storybook instead of Ladle.** Considered (Storybook is the
  industry standard). Rejected for this change: Ladle is
  Vite-native, single dev dep, faster dev experience, and
  adequate for the 5-component surface we have today. Storybook
  remains a future option if the catalog grows to >20 stories
  and we need addons.
- **Pre-commit hooks.** The Stylelint script and token-doc
  generator are wired as npm scripts. Wiring them into husky /
  pre-commit is a separate change.
- **Visual regression tests.** No screenshot regression harness
  exists; Ladle gives a stable URL for human eyeballing but
  does not assert pixel-level invariance.
- **Adding more rules than the five shipped.** The five chosen
  rule categories cover every spec rule that has been observed
  to regress in T2 review. Additional rules (e.g. "no inline
  styles", "no `!important`") can be added later.

## Decisions

### D1. Stylelint config is JSON, comments link rules to spec Requirements

`apps/web/.stylelintrc.json` documents each rule with a comment
that names the `design-system` Requirement it enforces:

```jsonc
{
  // F-3A.7 — enforces "Buttons declare their variant via className"
  "rules": {
    "selector-disallowed-list": [
      ".operation-list button",
      ".dashboard-refresh-action"
    ]
  }
}
```

**Rationale.** When a future contributor hits a Stylelint
violation, the comment tells them which spec rule they broke
and where to look. This makes the lint → spec → code chain
traceable.

**Alternatives considered.**

- *`.stylelintrc.js` with elaborate programmatic rules.*
  Rejected: harder to read; the five rule categories are all
  expressible with built-in Stylelint rules.
- *Stylelint plugin with custom logic for acid-lime
  reservation.* Rejected: the acid-lime rule is expressible as
  a `declaration-property-value-disallowed-list` with a
  selector-scoped whitelist. A plugin would be over-engineering.

### D2. Acid-lime rule is allowlist-based, not denylist-based

The Stylelint rule for acid-lime uses a whitelist of selectors
that are permitted to use `var(--color-acid-lime)` as a
declaration value:

- `.button-primary` class (the Bootstrap button fill, per F-104)
- `.backtest-run-form input:focus-visible` (focus ring)
- `.operation-link` (text decoration color)
- `.dashboard-load-state-loading` (text color)
- `.app-nav-link[aria-current="page"]` (the lime underline via
  `box-shadow: inset`)

**Rationale.** The acid-lime reservation rule is "lime fill
may appear at most once per view, on the per-view primary CTA".
The denylist approach ("ban lime everywhere except
button-primary") would over-block legitimate non-fill uses
(focus ring, underline). The allowlist approach is tighter and
matches the existing F-104 spec.

**Alternatives considered.**

- *Deny-list only the most common offenders.* Rejected: any
  future contributor would need to remember to add to the
  deny-list. The allow-list approach is self-documenting.
- *Ban `var(--color-acid-lime)` entirely.* Rejected: too
  aggressive; would break the focus-ring, underline, and
  SVG-stroke uses.

### D3. Ladle, not Storybook

Use `@ladle/react` (single dep) over Storybook (4–5 deps +
boilerplate).

**Rationale.** The app uses Vite. Ladle is Vite-native and
shares the same dev server. Storybook has more bells and
whistles (addon ecosystem) but for a 5-component surface the
added complexity is not justified. If the catalog grows past
20 stories and we need addon-level controls (accessibility,
viewport, theme), Storybook becomes the right answer; for now,
Ladle is the lighter fit.

**Alternatives considered.**

- *Storybook 8 with `@storybook/react-vite`.* Rejected: more
  deps, more config, slower dev startup, no current need for
  addons.
- *Hand-rolled component gallery (a single `/_gallery` route
  in the app).* Rejected: mixes catalog surface with
  production app; Ladle keeps them isolated.

### D4. Token reference doc generator is hand-rolled, no `style-dictionary`

Write `scripts/build-tokens-reference.mjs` (~50 lines, zero
deps) that parses `tokens.css` and emits `docs/tokens.md`.

**Rationale.** The original F-301 ask was "Style Dictionary
auto-sync from tokens.json". That JSON no longer exists; F-305
made `tokens.css` the source. The remaining need is
*discoverability*: developers need a machine-readable catalog
of the token surface. A 50-line Node script achieves this
without adding a 5 MB `style-dictionary` dependency to manage a
file that doesn't exist.

**Alternatives considered.**

- *Use `style-dictionary` with a custom parser that reads
  `tokens.css`.* Rejected: heavy dependency for a small job.
  `style-dictionary`'s value is JSON→CSS sync, which we don't
  need.
- *Hand-write `docs/tokens.md` and never regenerate.* Rejected:
  the doc would drift from the source immediately. The
  generator guarantees consistency.
- *Use a TSdoc / JSDoc generator on `tokens.ts`.* Rejected:
  the canonical source is CSS, not TS. Generating from CSS
  keeps one source of truth.

### D5. Generated `docs/tokens.md` is committed to git

Run the generator once, commit the output. Subsequent
`tokens.css` edits require re-running the generator and
committing the new output.

**Rationale.** Committed docs are visible to anyone who reads
the repo (no build step needed). Drift is detected by code
review (a contributor who changes `tokens.css` but doesn't
re-run the generator gets caught at review time). A future
change can wire the generator into pre-commit or CI.

**Alternatives considered.**

- *Generated file is `.gitignore`d.* Rejected: hides drift
  and forces every reader to run the generator.
- *Generated file is built in CI and published as an
  artifact.* Rejected: overkill for a single-file Markdown
  output.

### D6. Stylelint violations in current CSS are fixed in this change

The first Stylelint run on the current `styles.css` will
surface violations (e.g. any remaining literal border-radius,
any descendant-selector button styling). This change's tasks
include fixing each violation as part of the Stylelint
bring-up. Expected: ≤5 violations, all minor (literal
`9999px`, pre-existing `--app-nav` radius, etc.).

**Rationale.** Landing a lint rule that immediately fires on
the same PR would block merge. Better to land the rule + the
fixes together so the codebase is green from the first
commit.

**Alternatives considered.**

- *Land the rule first, fix violations in a follow-up.*
  Rejected: the rule is dead on arrival if the codebase
  doesn't pass it.
- *Disable the rule for existing violations.* Rejected:
  defeats the purpose; the rule is supposed to prevent
  regression, not just future regression.

## Risks / Trade-offs

- **Stylelint rule false positives**: the acid-lime allowlist
  needs to be exhaustive. A legitimate future use not in the
  allowlist would be flagged. → Mitigation: the allowlist is
  documented in the config JSON with comments; future
  contributors extend it intentionally.
- **Ladle dev dep weight**: 3 MB of node_modules. Acceptable
  for a dev-only dep. No production impact.
- **Token reference doc drift**: if `tokens.css` changes
  without re-running the generator, the doc is stale. →
  Mitigation: the spec scenario pins the file existence; a
  future change can wire the generator into CI.
- **Storybook not Storybook**: this is a one-way decision
  for now. Migrating from Ladle to Storybook later is
  straightforward (stories format is similar); the migration
  is mechanical, not architectural.
- **Header-text whitespace mismatch on archive-time merge** →
  Mitigation: spec uses only ADDED Requirements with new
  unique names, so no existing header needs verbatim
  re-typing.
