## Why

The web frontend now ships a complete design-system surface:
canonical tokens (T2.1), three-variant buttons (T1), radius
mapping (T2.2), feedback-accent rules (T1 + T2.2), a discrete
dashboard ladder (T2.2), and a state-component set (T2.3). Every
one of those rules lives in the `design-system` capability and
is enforced only by human review at PR time. None of it is
machine-checked.

Three Initiative issues remain that close that gap:

- **F-3A.7 Stylelint guard** — *design-system invariants are
  not machine-checked*. Today nothing prevents a contributor
  from reintroducing `.operation-list button { background: lime }`
  or a `line-height: 1.4` literal. The spec rules exist, but
  they fire only when a reviewer notices. A Stylelint config
  that encodes the canonical invariants turns those rules into
  a CI-failable check.

- **F-304 Storybook / Ladle component catalog** — *the state
  component set is not discoverable*. `Skeleton`, `ErrorBoundary`,
  `FeedbackMessage`, `EmptyState` were just added (T2.3) but a
  developer has to read the source to know they exist. A
  component catalog with controls (variant, width, etc.) makes
  the catalog self-documenting and gives QA a stable surface
  to eyeball changes against.

- **F-301 Style Dictionary / token tooling** — *the token
  surface has no machine-readable catalog*. `tokens.css` is the
  source of truth, but a developer asking "what `--space-*`
  values exist?" or "what color tokens are there?" has to read
  the whole file. F-301 was originally scoped as "Style
  Dictionary to auto-sync `tokens.json` → CSS variables"; that
  ask is **obsolete** because F-305 deleted `tokens.json` and
  made `tokens.css` canonical. The spirit of F-301 — *tooling
  that makes the token surface discoverable and verifiable* —
  is preserved with a lightweight Node script that parses
  `tokens.css` and emits a Markdown token reference. This
  achieves the discoverability / drift-detection goals without
  introducing a 5 MB `style-dictionary` dependency to manage a
  JSON file we no longer have.

Together, these three harden the design-system surface against
regression and make it discoverable. Stylelint goes first
because it has the highest leverage (one PR lands in CI
enforcement of all the rules the previous four changes shipped).

## What Changes

### Stylelint (F-3A.7)

Add `stylelint` + `stylelint-config-standard` to
`apps/web/package.json` devDependencies. Add a custom config at
`apps/web/.stylelintrc.json`. Add `npm --prefix apps/web run
lint:css` script that runs `stylelint "src/**/*.css"`.

Rules the config enforces (all derived from already-shipped
`design-system` capability requirements):

1. **No descendant-selector button styling.**
   `selector-disallowed-list` banning `.operation-list button`,
   `.dashboard-refresh-action`, `.operation-list > button`,
   `.operation-list button:hover`. Catches the pattern that
   triggered the T1 button-variant work.

2. **No literal numeric line-heights.**
   `declaration-property-value-disallowed-list` on `line-height`
   for plain number values. Catches the pattern that triggered
   the F-2.2 work in T2.2.

3. **No literal `border-radius` pixel values.**
   `declaration-property-value-disallowed-list` on `border-radius`
   for plain pixel values. Catches the F-103 hygiene issue
   (the one Loop 1 caught in T2.3).

4. **No `:root` declarations outside `tokens.css`.**
   File-level `overrides` exception that allows `:root` only in
   `apps/web/src/styles/tokens.css`. Catches future
   "I just need one custom property" drift.

5. **No raw `--color-acid-lime` outside an explicit allowlist.**
   Selector-scoped allowlist: `.button-primary`, input
   focus-visible rules, `.operation-link`,
   `.dashboard-load-state-loading`, and the
   `.app-nav-link[aria-current="page"]` underline. Enforces the
   F-104 acid-lime reservation rule.

The Stylelint config documents which existing `design-system`
Requirement each rule enforces (comments inline in the config
JSON). The script runs in CI; a failure is a blocker for merge.

### Ladle component catalog (F-304)

Add `@ladle/react` to `apps/web/package.json` devDependencies.
Add `apps/web/.ladle/config.mjs`. Add
`npm --prefix apps/web run ladle` script. Add a stories file
per state component:

- `apps/web/src/components/FeedbackMessage.stories.tsx`
- `apps/web/src/components/Skeleton.stories.tsx`
- `apps/web/src/components/ErrorBoundary.stories.tsx`
- `apps/web/src/components/EmptyState.stories.tsx`

Ladle dev server runs at `http://localhost:61000` by default
(Vite-compatible). The stories use the same components as
production — no runtime fork. The Vitest test gate is unaffected
(stories are dev-only).

### Token reference doc generator (F-301, re-scoped)

Add a Node script at `scripts/build-tokens-reference.mjs`
(~50 lines, zero deps). It parses
`apps/web/src/styles/tokens.css`, extracts the `:root { ... }`
block, and emits `docs/tokens.md` with one section per token
group (Colors, Surfaces, Typography families, etc.). The script
runs as `node scripts/build-tokens-reference.mjs` and is wired
into a `npm --prefix apps/web run build:tokens-doc` script. The
generated file is committed to git so it ships with the repo.

The script handles the alias chain (`var(--X)` values) by
recursively resolving and showing the resolved value alongside
the alias name.

### Spec

`design-system` capability gains three new Requirements:

1. *Design system invariants are enforced by Stylelint* (F-3A.7).
   Pins the file location of the config, the existence of the
   `lint:css` npm script, and the five rule categories above.
2. *Component catalog is reachable via Ladle* (F-304). Pins
   the `@ladle/react` dependency, the config file, and the
   existence of stories for each state component.
3. *Token reference doc is generated from tokens.css* (F-301,
   re-scoped). Pins the script location, the generated file
   path, and that the generator runs as part of the
   design-system surface.

No new tokens. No breaking changes to existing component APIs.
Stylelint config is additive (it will flag pre-existing
violations if any exist; those are addressed in this change's
tasks).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `design-system`:
  - **ADDED** Requirement: *Design system invariants are
    enforced by Stylelint* (F-3A.7)
  - **ADDED** Requirement: *Component catalog is reachable via
    Ladle* (F-304)
  - **ADDED** Requirement: *Token reference doc is generated
    from tokens.css* (F-301, re-scoped)

## Impact

- **Files**:
  - `apps/web/package.json` — +3 devDeps (`stylelint`,
    `stylelint-config-standard`, `@ladle/react`) + 3 new
    scripts (`lint:css`, `ladle`, `build:tokens-doc`)
  - `apps/web/.stylelintrc.json` — NEW
  - `apps/web/.ladle/config.mjs` — NEW
  - `apps/web/src/components/FeedbackMessage.stories.tsx` —
    NEW
  - `apps/web/src/components/Skeleton.stories.tsx` — NEW
  - `apps/web/src/components/ErrorBoundary.stories.tsx` — NEW
  - `apps/web/src/components/EmptyState.stories.tsx` — NEW
  - `scripts/build-tokens-reference.mjs` — NEW (~50 lines)
  - `docs/tokens.md` — NEW (generated; ~300 lines)
  - `openspec/specs/design-system/spec.md` — +3 Requirements
- **Risks**:
  - **Stylelint may flag pre-existing violations.** The first
    run will surface them; this change's tasks include a
    follow-up to either fix or document-allow each violation.
    Expected: ≤5 violations across the existing
    `apps/web/src/styles.css`.
  - **Ladle adds a dev dep** (`@ladle/react`, ~3 MB). The
    app bundle (Vite production build) is unaffected because
    Ladle is dev-only.
  - **Token reference doc drift**: if `tokens.css` changes
    without re-running the generator, `docs/tokens.md` is stale.
    Mitigation: the generator is a 1-second run; future change
    can wire it into a pre-commit hook or CI check.
