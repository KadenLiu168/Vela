## 1. Catalog foundation

- [x] 1.1 Create `apps/web/src/styles/tokens.css` with the
      contents of `/variables.css` (preserving the curated
      Linear subset already declared there)
- [x] 1.2 Fold the implementation-only tokens that today live
      only inside `apps/web/src/styles.css :root` into
      `tokens.css`: `--text-micro`, `--text-label`,
      `--text-body`, `--leading-body`,
      `--feedback-accent`, `--feedback-accent-loading`,
      `--feedback-accent-success`, `--feedback-accent-error`,
      `--feedback-accent-info`, `--feedback-accent-empty`,
      `--focus-ring-color`, `--radius-cards`, `--radius-pills`,
      `--surface-slate`
- [x] 1.3 Rename the monospace font token declaration inside
      `tokens.css` from `--font-jetbrains-mono` to
      `--font-berkeley-mono`, and chain its value to
      `'JetBrains Mono', 'Berkeley Mono', ui-monospace,
      SFMono-Regular, Menlo, Monaco, Consolas, monospace`
      in that exact order
- [x] 1.4 Add a leading comment block to `tokens.css`
      listing the token groups (Colors, Surfaces, Typography,
      Spacing, Radius, Shadow, Feedback accents, Layout, Motion)
- [x] 1.5 Verify `/variables.css` is unchanged at this commit
      (the half-applied rename stays; the file is then deleted
      in step 4.1)

## 2. Wire tokens.css into the build

- [x] 2.1 Prepend `@import "./styles/tokens.css";` to the top
      of `apps/web/src/styles.css`, before any other rule
- [x] 2.2 Delete the entire `:root { ... }` block from
      `apps/web/src/styles.css` (do not delete `@font-face`
      rules; they stay in `styles.css` so the browser can load
      the woff2 files)
- [x] 2.3 Confirm `apps/web/src/styles.css` no longer contains
      any CSS custom property declaration
- [x] 2.4 Confirm no other `.css` file under `apps/web/src/`
      declares a `:root { ... }` block

## 3. Complete F-002 font rename

- [x] 3.1 In `apps/web/src/styles.css`, replace every
      `var(--font-jetbrains-mono)` with
      `var(--font-berkeley-mono)` (5 expected sites based on
      the current stylesheet)
- [x] 3.2 Run
      `grep -rn "var(--font-jetbrains-mono)" apps/web/src`
      and confirm zero hits before proceeding

## 4. Cleanup

- [x] 4.1 Delete `/variables.css` from the repo root
- [x] 4.2 Rewrite `docs/token-source.md`:
      remove the `DESIGN.md` and `tokens.json` paragraphs
      (the files no longer exist); remove the
      `variables.css` paragraph (the role has moved);
      describe `apps/web/src/styles/tokens.css` as the
      canonical implementation source

## 5. Validation

- [x] 5.1 `openspec validate add-design-system-spec` passes
- [x] 5.2 `npm --prefix apps/web run typecheck` passes
- [x] 5.3 `npm --prefix apps/web run lint` passes
- [x] 5.4 `npm --prefix apps/web run test` passes
- [x] 5.5 `npm --prefix apps/web run build` passes
- [x] 5.6 Built-CSS verification (CLI-env equivalent of the
      dev-server smoke because no browser is available here):
      the production bundle at
      `apps/web/dist/assets/index-*.css` contains exactly
      one `:root` rule (the one from `tokens.css`); the
      monospace value resolves to `JetBrains Mono` →
      `Berkeley Mono`; zero stale `var(--font-jetbrains-mono)`
      references; five `var(--font-berkeley-mono)` references
      in `styles.css`. Manual browser smoke deferred to merge.

## 6. Spec sync and archive

- [x] 6.1 `openspec-archive-change add-design-system-spec`
      archives the change and lands
      `openspec/specs/design-system/spec.md` as a new
      top-level capability
- [x] 6.2 `openspec validate design-system` passes against
      the archived spec
