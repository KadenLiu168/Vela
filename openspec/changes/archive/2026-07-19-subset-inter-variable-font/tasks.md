## 1. Subsetting Toolchain

- [x] 1.1 Capture a pre-change browser baseline for the Dashboard, Command
  Palette, and a mixed ETF name at weights `300`, `400`, `510`, and `590`;
  record the current font request URL, 345,588-byte payload, request duration,
  text wrapping, and the six required UI symbols.
- [x] 1.2 Add `fonttools[woff]==4.63.0` to the root development dependency
  group and refresh `uv.lock`, locking the WOFF2/Brotli toolchain.
- [x] 1.3 Copy the exact current Inter 4.0 input to
  `scripts/fonts/inter/InterVariable-source.woff2`, add the upstream OFL 1.1
  license, and record/verify SHA-256
  `8af7bd5b545567adffb3dfceb5bedb353a522d7bf1b3a2b8af7b6064156babc0`.
  Keep the existing public font in place until the subset and consumer
  references are ready.
- [x] 1.4 Add a reviewed Unicode manifest for `U+0020–00FF`,
  `U+0300–036F`, and the explicit punctuation/symbol ranges defined by the
  design. Require every explicit UI symbol to exist in the source cmap; allow
  unmapped control positions inside block ranges.
- [x] 1.5 Add `scripts/fonts/inter/subset_inter_variable.py` and document the
  repository-root command
  `uv run python scripts/fonts/inter/subset_inter_variable.py` in
  `scripts/README.md`. The script MUST accept an optional output path for
  temporary test generation, verify the source hash, read the manifest,
  retain `opsz`/`wght`, preserve
  `ccmp,kern,mark,mkmk,cv01,ss03,zero,calt`, and fail rather than silently
  changing the 98,304-byte contract.

## 2. Font Contract Tests

- [x] 2.1 Add `tests/test_inter_font.py` with a failing check for a valid WOFF2,
  the 98,304-byte ceiling, source-matching `opsz`/`wght` axes, absence of
  `ital`/`slnt`, and CSS usability at `300`, `400`, `510`, and `590`.
- [x] 2.2 Add failing cmap checks for representative Basic Latin, Latin-1,
  combining coverage, and `·`, `—`, `…`, `⌘`, `✓`, and `✗`; also check
  representative Greek, Cyrillic, Latin Extended, IPA, and Vietnamese
  precomposed code points are excluded.
- [x] 2.3 Add failing layout-table checks proving
  `ccmp`, `kern`, `mark`, `mkmk`, `cv01`, `ss03`, `zero`, and `calt` remain
  available for retained glyphs.
- [x] 2.4 Add failing reproducibility checks for the source SHA/license,
  byte-identical repeated generation, and equality between a fresh temporary
  generation and the committed served subset.
- [x] 2.5 Add failing declaration/asset checks requiring the CSS font URL, the
  normalized CSS `unicode-range`, HTML preload, and committed manifest to
  agree, with exactly one served font under `apps/web/public/fonts/`.

## 3. Generate and Integrate the Subset

- [x] 3.1 Generate and commit
  `apps/web/public/fonts/InterVariable-latin.woff2`, then make the binary,
  coverage, layout, and reproducibility tests pass without relaxing the
  manifest, required features, variable axes, or size budget.
- [x] 3.2 Update the Inter Variable `@font-face` to reference the subset, declare the manifest-aligned `unicode-range`, and preserve normal style, `font-display: swap`, feature behavior, and the `300–700` weight range.
- [x] 3.3 Update the single font preload in `apps/web/index.html` to reference the subset.
- [x] 3.4 Update the font asset comment in `apps/web/src/styles.css`; verify
  `/fonts/InterVariable.woff2` has no frontend source reference, delete its
  former public copy, and verify the full font exists only as the non-public
  canonical generation input.
- [x] 3.5 Verify no IBM Plex Mono font file, `@font-face`, preload, or leading
  `--font-display` entry is introduced while the superseded IBM Plex Mono
  requirement is removed from the post-archive `design-system` contract.

## 4. Verification

- [x] 4.1 Run `uv run pytest tests/test_inter_font.py`, then the existing
  `npm --prefix apps/web run test`, `typecheck`, `lint`, `lint:css`, and
  `lint:css:root` suites.
- [x] 4.2 Run `npm --prefix apps/web run build` and verify
  `apps/web/dist/fonts/` contains only `InterVariable-latin.woff2`, within
  98,304 bytes, with no stale full-font asset.
- [x] 4.3 In a browser, compare against the task 1.1 baseline and verify
  retained Latin text, weights `300`, `400`, `510`, and `590`, enabled
  OpenType features, and all six required UI symbols have no text wrapping,
  clipping, missing-glyph, or visible outline regression.
- [x] 4.4 Render a mixed Chinese ETF name such as `沪深300ETF` and verify the Chinese glyphs use system fallback, the Latin suffix uses Inter Variable, the text remains legible without overflow, and no additional project-hosted font request occurs.
- [ ] 4.5 Under a Slow 4G profile with cache disabled, record the subset
  response payload, request duration, and before/after byte delta; verify
  exactly one successful subset-font request, a payload no larger than
  98,304 bytes, and no font-related HTTP or console error. Do not claim a
  first-paint, LCP, or TTI improvement unless separately measured.
- [x] 4.6 Run
  `openspec validate subset-inter-variable-font --type change --strict
  --no-interactive` and require a clean result before Apply is considered
  complete.
