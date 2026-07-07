## 1. Spec additions

- [ ] 1.1 Append the two new Requirements (radius mapping + dashboard
      ladder) and their Scenarios into
      `openspec/specs/design-system/spec.md` at archive time. The
      delta file `specs/design-system/spec.md` in this change
      directory is the source of truth; `openspec archive` merges
      it under the `## ADDED Requirements` heading.
- [ ] 1.2 Append the one new Requirement (EmptyAction variant-aware)
      and its Scenarios into
      `openspec/specs/web-frontend-app/spec.md` at archive time.

## 2. F-103 — Nav loses its capsule

- [ ] 2.1 In `apps/web/src/styles.css`, change
      `.app-nav-link { border-radius: var(--radius-pills); }`
      to `border-radius: var(--radius-md);` (the new soft-tile
      radius). Leave all other declarations on `.app-nav-link`
      untouched.
- [ ] 2.2 In `apps/web/src/styles.css`, change
      `.app-nav { border-radius: var(--radius-pills); }` to
      `border-radius: var(--radius-md);`. The whole nav
      (container + links) leaves the capsule per F-103's
      "remove capsule from nav" intent.

## 3. F-106 — Status pills consume `--feedback-accent-*`

- [ ] 3.1 In `apps/web/src/styles.css`, replace
      `.status-pill-success { color: var(--color-pulse-green); }`
      with `.status-pill-success { color: var(--feedback-accent-success); }`.
- [ ] 3.2 Replace
      `.status-pill-partial { color: var(--color-signal-teal); }`
      with `.status-pill-partial { color: var(--feedback-accent-info); }`.
- [ ] 3.3 Replace
      `.status-pill-error { color: var(--color-coral-red); }`
      with `.status-pill-error { color: var(--feedback-accent-error); }`.
- [ ] 3.4 Replace
      `.status-pill-neutral { color: var(--color-ash); }`
      with `.status-pill-neutral { color: var(--feedback-accent-empty); }`
      (visual change: neutral pill darkens from `#62666d` to `#383b3f`).

## 4. F-201 — Dashboard heading discrete ladder

- [ ] 4.1 In `apps/web/src/styles.css`, replace
      `font-size: clamp(var(--text-heading), 6vw, var(--text-display));`
      on `.dashboard-heading h1` with a base `font-size: var(--text-heading);`.
- [ ] 4.2 Add a `@media (min-width: 768px)` block (immediately
      after the `.dashboard-heading h1` rule) containing
      `.dashboard-heading h1 { font-size: var(--text-heading-lg); }`.
- [ ] 4.3 Add a `@media (min-width: 1280px)` block (immediately
      after the 768 px block) containing
      `.dashboard-heading h1 { font-size: var(--text-display); }`.
- [ ] 4.4 Delete the redundant `.dashboard-heading h1 { font-size: var(--text-heading); ... }`
      declaration inside the mobile @media block
      (`@media (max-width: 640px)` or equivalent around
      `styles.css:1269`). Confirm with a grep before deleting
      that no other rule depends on that declaration.

## 5. F-2.2 — Magic line-heights become tokens

- [ ] 5.1 In `apps/web/src/styles/tokens.css`, add `--leading-snug: 1.4;`
      to the "4. Typography scale" group, immediately after
      `--leading-body: 1.5;`.
- [ ] 5.2 In `apps/web/src/styles.css`, change
      `.app-nav-link { line-height: 1; }` to
      `line-height: var(--leading-heading);`.
- [ ] 5.3 In `apps/web/src/styles.css`, change
      `.workflow-grid strong, .detail-page dd { line-height: 1.4; }`
      to `line-height: var(--leading-snug);`.

## 6. F-3A.9 — `EmptyAction` accepts a `variant` prop

- [ ] 6.1 In `apps/web/src/pages/DashboardPage.tsx`, extend the
      `EmptyAction` function's parameter list (around line 818)
      with a `variant` parameter:
      ```ts
      variant?: "button-primary" | "button-secondary" | "button-tertiary"
      ```
      Default the parameter to `"button-secondary"`.
- [ ] 6.2 In the same function, change the rendered `<button>`
      `className="button-secondary"` to `className={variant}`.
- [ ] 6.3 Verify the two existing call sites (around lines 263
      and 629) continue to render `button-secondary` because
      they do not pass an explicit `variant` prop (the default
      fires).
- [ ] 6.4 Run `npm --prefix apps/web run typecheck` and confirm
      no new type errors are introduced (the `variant` prop
      is optional with a default, so existing call sites must
      type-check unchanged).

## 7. Validation

- [ ] 7.1 Run `openspec validate design-system-component-polish`
      and confirm exit 0.
- [ ] 7.2 Run `openspec validate design-system` and confirm the
      merged capability still validates (post-archive).
- [ ] 7.3 Run `openspec validate web-frontend-app` and confirm
      the merged capability still validates (post-archive).
- [ ] 7.4 Run `npm --prefix apps/web run typecheck` — exit 0.
- [ ] 7.5 Run `npm --prefix apps/web run lint` — exit 0.
- [ ] 7.6 Run `npm --prefix apps/web run test` — exit 0
      (existing tests do not assert nav radius, pill color, or
      heading font-size; expected to be unchanged).
- [ ] 7.7 Run `npm --prefix apps/web run build` — exit 0;
      CSS bundle size delta expected < 200 B (the only new
      declaration is `--leading-snug`).
- [ ] 7.8 Run `uv run pytest -q` from the repo root — 417 passed.
- [ ] 7.9 Eyeball the Dashboard, Signal Detail, and Backtest
      Detail routes in the running dev server and confirm:
      nav links are rounded tiles (not capsules);
      Dashboard heading steps 48 / 64 / 72 at 640 / 768 / 1280 px
      breakpoints;
      status pills use the canonical accent colors;
      empty-state buttons still render `button-secondary`.

## 8. Commit and push

- [ ] 8.1 `git status` shows only
      `apps/web/src/styles.css`,
      `apps/web/src/styles/tokens.css`,
      `apps/web/src/pages/DashboardPage.tsx`,
      `openspec/specs/design-system/spec.md`,
      `openspec/specs/web-frontend-app/spec.md`, and
      the contents of `openspec/changes/design-system-component-polish/`.
- [ ] 8.2 `git add` those files explicitly (no `git add .`).
- [ ] 8.3 `git commit -m "feat(design-system): polish components (F-103 / F-106 / F-201 / F-2.2 / F-3A.9)"`
      (Conventional Commits, scoped to design-system, references
      the five Initiative issues in the body).
- [ ] 8.4 `git push origin main`.
