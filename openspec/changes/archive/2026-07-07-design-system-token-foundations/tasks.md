## 1. Spacing ladder

- [ ] 1.1 Add the 8px-grid semantic ladder to `apps/web/src/styles/tokens.css`:
      declare `--space-xs`, `--space-sm`, `--space-md`, `--space-lg`,
      `--space-xl`, `--space-2xl`, `--space-3xl` as `var(--spacing-8)`,
      `var(--spacing-16)`, `var(--spacing-24)`, `var(--spacing-32)`,
      `var(--spacing-48)`, `var(--spacing-64)`, `var(--spacing-96)`
      respectively, placed in the existing "6. Spacing" group.
- [ ] 1.2 Prune the two declared-but-unused primitives `--spacing-28`
      and `--spacing-140` from `tokens.css`. Verify with
      `grep -RE "var\(--spacing-(28|140)\)" apps/web/src/` returns
      no matches before deleting.
- [ ] 1.3 Update the leading comment block in `tokens.css` so the
      "6. Spacing" group description mentions the new `--space-*`
      ladder as the preferred layout-gap alias.

## 2. Type scale

- [ ] 2.1 Add `--text-14`, `--text-16`, `--text-17` to
      `apps/web/src/styles/tokens.css` (in the "4. Typography scale"
      group), each with the matching `--leading-14`, `--leading-16`,
      `--leading-17` resolving to `1.5`.
- [ ] 2.2 Update `--text-body` value from `15px` → `16px` and
      `--leading-body` value from `1.6` → `1.5`. Do not rename the
      token; consumers continue to read `var(--text-body)` /
      `var(--leading-body)` and automatically pick up the new values.
- [ ] 2.3 Verify with
      `grep -nE "var\(--text-body\)|var\(--leading-body\)" apps/web/src/styles.css`
      that exactly 4 call sites exist (no rename needed); eyeball each
      site during the apply-loop review to confirm the new
      `16px / 1.5` does not overflow its container.

## 3. Inter Variable OpenType features

- [ ] 3.1 Add `--font-feature-settings-default: "cv01", "ss03", "zero", "calt";`
      to `apps/web/src/styles/tokens.css` (new "12. Font features"
      group, between "4. Typography scale" and "5. Font weights").
- [ ] 3.2 Add a single `body { font-feature-settings: var(--font-feature-settings-default); }`
      rule to `apps/web/src/styles.css`, placed immediately after
      the `@import "./tokens.css";` line so it follows the import
      order and operates on default text only.
- [ ] 3.3 Update the leading comment block in `tokens.css` to add
      "12. Font features" to the listed groups.

## 4. Card tokens

- [ ] 4.1 Add a new "13. Card primitives" group to
      `apps/web/src/styles/tokens.css` declaring
      `--card-bg`, `--card-border-color`, `--card-padding-x`,
      `--card-padding-y`, `--card-radius`, `--card-shadow`,
      `--card-gap` with the values documented in
      `openspec/changes/design-system-token-foundations/design.md`
      (Section D4).
- [ ] 4.2 Update the leading comment block in `tokens.css` to add
      "13. Card primitives" to the listed groups.
- [ ] 4.3 Do NOT migrate any `styles.css` card selector in this
      change. Verify with
      `grep -nE "var\(--card-" apps/web/src/styles.css` returns
      no matches at archive time — the tokens are declared but
      unused, by design.

## 5. Spec delta

- [ ] 5.1 Append the four new Requirements (Spacing ladder / Type
      scale / Inter Variable features / Card primitives) into the
      canonical `openspec/specs/design-system/spec.md` at archive
      time. The delta file
      `openspec/changes/design-system-token-foundations/specs/design-system/spec.md`
      is the source of truth for the appended text; `openspec archive`
      merges it under the `## ADDED Requirements` heading.

## 6. Validation

- [ ] 6.1 Run `openspec validate design-system-token-foundations`
      and confirm exit 0.
- [ ] 6.2 Run `openspec validate design-system` and confirm the
      merged capability still validates (this happens post-archive).
- [ ] 6.3 Run `npm --prefix apps/web run typecheck` — exit 0.
- [ ] 6.4 Run `npm --prefix apps/web run lint` — exit 0.
- [ ] 6.5 Run `npm --prefix apps/web run test` — exit 0 (existing
      snapshot tests pick up the new font-size and feature-settings
      values automatically; no test edits expected).
- [ ] 6.6 Run `npm --prefix apps/web run build` — exit 0; CSS bundle
      size expected to grow by < 1 KB from the new declarations.
- [ ] 6.7 Run `uv run pytest -q` from the repo root — 417 passed.
- [ ] 6.8 Eyeball the Dashboard, Signal Detail, and Backtest Detail
      routes in the running dev server and confirm:
      body text now renders at 16px / 1.5;
      lowercase `a` is single-storey;
      digit `0` is slashed;
      no card overflow or layout shift.

## 7. Commit and push

- [ ] 7.1 `git status` shows only
      `apps/web/src/styles/tokens.css`,
      `apps/web/src/styles.css`,
      `openspec/specs/design-system/spec.md`, and
      the contents of `openspec/changes/design-system-token-foundations/`.
- [ ] 7.2 `git add` those files explicitly (no `git add .`).
- [ ] 7.3 `git commit -m "feat(design-system): add token foundations (F-101/F-102/F-302/F-303)"`
      (Conventional Commits, scoped to design-system, references the
      four Initiative issues in the body).
- [ ] 7.4 `git push origin main`.
