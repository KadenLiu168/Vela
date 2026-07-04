## 1. Reference files

- [x] 1.1 Overwrite `DESIGN.md` with the contents of
      `DESIGN_Linear.md`; remove `DESIGN_Linear.md` after
      the swap
- [x] 1.2 Overwrite `tokens.json` with the contents of
      `tokens_Linear.json`; remove `tokens_Linear.json` after
      the swap
- [x] 1.3 Overwrite `variables.css` with the contents of
      `variables_Linear.css`; remove `variables_Linear.css` after
      the swap

## 2. Self-hosted fonts

- [x] 2.1 Create `apps/web/public/fonts/`
- [x] 2.2 Download `InterVariable.woff2` (OFL, single file
      variable font covering weights 300–700) from
      https://github.com/rsms/inter/releases and place in
      `apps/web/public/fonts/`
- [x] 2.3 Download `JetBrainsMono-Regular.woff2` and
      `JetBrainsMono-Medium.woff2` from the JetBrains Mono
      GitHub release and place in `apps/web/public/fonts/`
- [x] 2.4 In `apps/web/src/styles.css`, add `@font-face`
      blocks at the top referencing both woff2 files with
      `font-display: swap`
- [x] 2.5 In `apps/web/index.html`, remove the Google Fonts
      `<link>` and the `preconnect` hints; add a
      `<link rel="preload" href="/fonts/InterVariable.woff2"
      as="font" type="font/woff2" crossorigin>` in `<head>`

## 3. styles.css :root rewrite

- [x] 3.1 Replace the entire `:root` block in
      `apps/web/src/styles.css` with the Linear token set,
      keeping the three Ventriloc-only typography tokens
      (`--text-micro`, `--text-label`, `--text-body`)
      re-pointed to Linear semantic sources
- [x] 3.2 Update layout numbers:
      `--section-gap: 96px`, `--card-padding: 24px`,
      `--element-gap: 8px`
- [x] 3.3 Update radius scale per Linear:
      `--radius-sm: 2px`, `--radius-md: 6px`,
      `--radius-xl: 12px`, `--radius-2xl: 16px`,
      `--radius-2xl-2: 22px`, `--radius-full: 400px`,
      `--radius-full-2: 9999px`
- [x] 3.4 Add the 8 Linear shadow tokens to `:root`
      (`--shadow-sm`, `--shadow-md`, `--shadow-subtle`,
      `--shadow-subtle-2`, `--shadow-subtle-3`,
      `--shadow-xl`, `--shadow-subtle-4`, `--shadow-subtle-5`)
- [x] 3.5 Remove `--radius-asymmetric-card`,
      `--radius-tags`, `--radius-cards`, `--radius-buttons`,
      `--radius-nav-pills` from `:root` (their roles move to
      `--radius-pills`, `--radius-2xl-2`, `--radius-cards`,
      `--radius-md`, `--radius-pills`)

## 4. styles.css consumer remap (136 references)

- [x] 4.1 Replace `var(--color-graphite)` used as
      **text/heading** with `var(--color-paper)`; used as
      **button fill** with `var(--color-acid-lime)`; used as
      **focus ring or load/error** with `var(--color-acid-lime)`
      or `var(--color-iris-violet)` per role
- [x] 4.2 Replace `var(--color-canvas-white)` with
      `var(--surface-void)` (page) or
      `var(--color-paper)` (text-on-fill)
- [x] 4.3 Replace `var(--color-ash)` (card bg) with
      `var(--surface-carbon)`; verify each call site
- [x] 4.4 Replace `var(--color-ivory)` (warm accent bg) with
      `var(--surface-obsidian)`
- [x] 4.5 Replace `var(--color-steel)` with
      `var(--color-mist)`
- [x] 4.6 Replace `var(--color-slate)` with
      `var(--color-fog)`
- [x] 4.7 Replace `var(--color-mist)` (hairline) with
      `var(--color-graphite)` (Linear graphite = border)
- [x] 4.8 Replace `var(--color-ember-orange)` (focus ring /
      link) with `var(--color-acid-lime)`
- [x] 4.9 Replace `var(--color-brass)` with
      `var(--color-pulse-green)` / `var(--color-acid-lime)`
- [x] 4.10 Replace `var(--font-polysans)` and
       `var(--font-inter)` (non-mono) with
       `var(--font-inter-variable)`
- [x] 4.11 Replace `var(--radius-buttons)` (was 0px) with
       `var(--radius-md)` (6px)
- [x] 4.12 Replace `var(--radius-tags)` with
       `var(--radius-2xl-2)`
- [x] 4.13 Replace `var(--radius-nav-pills)` with
       `var(--radius-pills)`
- [x] 4.14 Remove every reference to
       `var(--radius-asymmetric-card)`
- [x] 4.15 Apply `--shadow-subtle-4` to elevated card
       surfaces; apply `--shadow-md` to the floating nav
       container

## 5. Validation

- [x] 5.1 Run OpenSpec validation for the change and specs
- [x] 5.2 `npm --prefix apps/web run typecheck`
- [x] 5.3 `npm --prefix apps/web run lint`
- [x] 5.4 `npm --prefix apps/web run test`
- [x] 5.5 `npm --prefix apps/web run build`
- [x] 5.6 Dev-server smoke test (HTTP 200, preload link
      present, InterVariable.woff2 served at
      `/fonts/InterVariable.woff2` with 200 + 345588 bytes).
      Full visual QA at 1280/1024/900/720px deferred to
      human reviewer before sign-off.

## 6. Spec sync and archive

- [x] 6.1 Apply delta spec from
      `openspec/changes/2026-07-04-migrate-web-to-linear-design-system/specs/web-frontend-app/spec.md`
      to `openspec/specs/web-frontend-app/spec.md` using
      `openspec-sync-specs`; cleaned up residual Ventriloc
      token references in non-delta requirements so the spec
      describes the Linear system end-to-end
- [x] 6.2 Archive the change via `openspec-archive-change`
      after all tasks 1–5 are checked
