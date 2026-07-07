## 1. Stylelint bring-up (F-3A.7)

- [ ] 1.1 In `apps/web/package.json`, add `stylelint` and
      `stylelint-config-standard` to `devDependencies`. Add a
      new script entry `lint:css` that runs
      `stylelint "src/**/*.css"`.
- [ ] 1.2 Create `apps/web/.stylelintrc.json` extending
      `stylelint-config-standard` and declaring the five rule
      categories:
      - `selector-disallowed-list` for `.operation-list button`
        and friends (rule category 1)
      - `declaration-property-value-disallowed-list` for
        `line-height` numeric values (rule category 2)
      - `declaration-property-value-disallowed-list` for
        `border-radius` pixel values (rule category 3)
      - file-level exclusion for `:root` outside `tokens.css`
        via the `overrides` mechanism (rule category 4)
      - `declaration-property-value-disallowed-list` (with
        selector-scoped overrides) for `var(--color-acid-lime)`
        outside the allowlist (rule category 5)
- [ ] 1.3 Run `npm --prefix apps/web run lint:css` once.
      Expect ≤5 violations in the current `styles.css`. Fix
      each violation in-place (replace literals with tokens,
      move declarations to allowed contexts).
- [ ] 1.4 Run `npm --prefix apps/web run lint:css` again and
      confirm exit 0.

## 2. Token reference doc generator (F-301, re-scoped)

- [ ] 2.1 Create `scripts/build-tokens-reference.mjs`. The
      script:
      - reads `apps/web/src/styles/tokens.css`
      - extracts the `:root { ... }` block
      - walks each `--name: value;` declaration
      - groups by the preceding `/* N. Section — comment */`
        marker
      - resolves `var(--X)` aliases recursively (with cycle
        detection)
      - emits Markdown to `docs/tokens.md`
      - uses only Node built-ins (`fs`, `path`)
- [ ] 2.2 In `apps/web/package.json`, add the
      `build:tokens-doc` script:
      `node ../../scripts/build-tokens-reference.mjs`.
- [ ] 2.3 Run `npm --prefix apps/web run build:tokens-doc`
      once and confirm `docs/tokens.md` is generated and
      contains all token groups.
- [ ] 2.4 Commit `docs/tokens.md` to the repository.

## 3. Ladle component catalog (F-304)

- [ ] 3.1 In `apps/web/package.json`, add `@ladle/react` to
      `devDependencies`. Add the `ladle` script:
      `ladle dev`.
- [ ] 3.2 Create `apps/web/.ladle/config.mjs` declaring the
      stories directory (`src/components`) and any provider
      wrappers (none required for the current components).
- [ ] 3.3 Create
      `apps/web/src/components/FeedbackMessage.stories.tsx`
      with one story per variant plus a default.
- [ ] 3.4 Create
      `apps/web/src/components/Skeleton.stories.tsx` with
      text default, block variants, and circle diameter
      variations.
- [ ] 3.5 Create
      `apps/web/src/components/ErrorBoundary.stories.tsx`
      with happy path, default fallback, and a custom
      fallback story.
- [ ] 3.6 Create
      `apps/web/src/components/EmptyState.stories.tsx` with
      a default empty-state story and one paired with an
      inline `EmptyAction` for context.
- [ ] 3.7 Run the Ladle build (or equivalent catalog build)
      and confirm no compile errors.
- [ ] 3.8 Confirm `npm --prefix apps/web run build` (the
      production Vite build) still works and the bundle size
      delta is < 5 KB (Ladle is dev-only).

## 4. Spec delta

- [ ] 4.1 Append the three new Requirements ("Design system
      invariants are enforced by Stylelint", "Component
      catalog is reachable via Ladle", "Token reference doc
      is generated from tokens.css") and their scenarios into
      `openspec/specs/design-system/spec.md` at archive time.
      The delta file is the source of truth; `openspec
      archive` merges it under the `## ADDED Requirements`
      heading.

## 5. Validation

- [ ] 5.1 Run `openspec validate design-system-infrastructure`
      and confirm exit 0.
- [ ] 5.2 Run `openspec validate design-system` (post-archive)
      and confirm the merged capability still validates.
- [ ] 5.3 Run `npm --prefix apps/web run typecheck` — exit 0.
- [ ] 5.4 Run `npm --prefix apps/web run lint` — exit 0
      (ESLint).
- [ ] 5.5 Run `npm --prefix apps/web run lint:css` — exit 0
      (NEW; this is the Stylelint gate).
- [ ] 5.6 Run `npm --prefix apps/web run test` — exit 0;
      expected 71 passed / 7 skipped (unchanged).
- [ ] 5.7 Run `npm --prefix apps/web run build` — exit 0;
      CSS bundle delta expected < 1 KB (Stylelint and Ladle
      are dev-only).
- [ ] 5.8 Run `npm --prefix apps/web run build:tokens-doc` and
      confirm `docs/tokens.md` regenerates.
- [ ] 5.9 Run `uv run pytest -q` from the repo root — 417
      passed (no backend changes).
- [ ] 5.10 Eyeball `npm --prefix apps/web run ladle` in dev
      and confirm the catalog renders all four stories.

## 6. Commit and push

- [ ] 6.1 `git status` shows only:
      `apps/web/package.json`,
      `apps/web/package-lock.json` (auto-updated),
      `apps/web/.stylelintrc.json` (new),
      `apps/web/.ladle/config.mjs` (new),
      `apps/web/src/components/*.stories.tsx` (4 new),
      `scripts/build-tokens-reference.mjs` (new),
      `docs/tokens.md` (new, generated),
      `openspec/specs/design-system/spec.md` (modified),
      `openspec/changes/archive/2026-07-07-design-system-infrastructure/`
      (new).
- [ ] 6.2 `git add` those files explicitly (no `git add .`).
- [ ] 6.3 `git commit -m "feat(design-system): infrastructure (F-3A.7 / F-301 / F-304)"`
      (Conventional Commits, scoped to design-system,
      references the three Initiative issues in the body).
- [ ] 6.4 `git push origin main`.
