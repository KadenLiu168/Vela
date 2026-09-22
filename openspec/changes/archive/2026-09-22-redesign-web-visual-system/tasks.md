## 1. Baseline and Contract Guards

- [x] 1.1 Re-run `git status`, `openspec list --json`, and `openspec validate redesign-web-visual-system --strict`; record the clean/owned baseline and verify no unrelated Change or user work is touched.
- [x] 1.2 Add or update concentrated static contract tests for the semantic token groups, exact values, font roles, font resources/preloads, and forbidden legacy tokens; verify the new assertions fail against the pre-migration runtime.
- [x] 1.3 Update `seriesColor.test.ts` expectations to the six `--chart-series-*` roles while retaining stable-key and deterministic-fallback assertions; verify the focused test fails before the resolver migration.

## 2. Geist Font Runtime

- [x] 2.1 Vendor the official Geist v1.7.2 Sans and Mono variable WOFF2 resources under `apps/web/public/fonts/`, add the official OFL/provenance record under `scripts/fonts/geist/`, and verify both SHA-256 values and `wght 100–900` metadata match the design.
- [x] 2.2 Replace the Inter `@font-face` rule and preload with matching Geist Sans/Mono declarations and exactly two preloads; verify static font tests and a production build resolve both files without font-related errors.
- [x] 2.3 Remove the served Inter subset and `scripts/fonts/inter/` source/tooling only after Geist verification succeeds; verify no Inter font file, preload, `@font-face`, or Inter-specific feature/axis contract remains.
- [x] 2.4 Replace `tests/test_inter_font.py` with Geist font-contract coverage using existing FontTools; verify both binary hashes, WOFF2/family/axis metadata, OFL, glyph/fallback coverage, preload/font-face linkage, `font-display: swap`, and asset inventory. Update only the font section of `scripts/README.md`; run the focused replacement Python test before removing obsolete subset coverage.

## 3. Canonical Semantic Tokens

- [x] 3.1 Rebuild the color section of `tokens.css` with the exact surface, border, text, interaction, status, market, and chart roles from the delta spec; verify concentrated token tests resolve every exact value.
- [x] 3.2 Replace the three legacy font aliases with `--font-sans` and `--font-mono`, including the required Chinese/system fallback chains; verify font-token tests and source grep find no legacy font declaration.
- [x] 3.3 Replace the old display/type ladder with the exact research-workstation role sizes, `--leading-*` pairs, weights, and four card data rungs; verify every retained typography token has a consumer and all CSS line heights remain token-based.
- [x] 3.4 Rebase shared card, feedback, focus, shadow, and other visual aliases onto the new semantic roles without changing spacing/radius contracts; verify aliases resolve through the token-reference parser and no component-specific palette is introduced.

## 4. Global Surfaces, Interaction, and Typography

- [x] 4.1 Migrate body, AppShell, page headings, navigation, focus, and brand styling to Celestial Research roles and the 22px subordinate brand treatment; verify App navigation tests still preserve skip-link, `aria-current`, and main-focus behavior.
- [x] 4.2 Migrate primary, secondary, tertiary, and pressed button states to interaction/surface/border/text roles while preserving exactly three variants and one prominent primary CTA per view; verify existing button and `aria-pressed` component tests pass.
- [x] 4.3 Migrate cards, panels, dialogs, inputs, lists, and tables to canvas/panel/raised/hover surfaces and subtle/strong borders; verify changed selectors use semantic tokens and do not introduce shadow-led hierarchy.
- [x] 4.4 Apply Sans to language/UI content and Mono plus tabular numerals to quantitative/code-like roles, including mixed-content tables, description lists, forms, and Command Palette values; use narrow semantic classes or spans where required without changing accessible names or behavior. Verify names/descriptions remain Sans, symbols/dates/returns/parameters use Mono, and compact-list `dt`/`dd` share `--leading-body-card: 20px` with aligned baselines.
- [x] 4.5 Replace literal transitions only in selectors touched by this migration with the existing duration/easing tokens; verify CSS lint finds no new motion-vocabulary violation and reduced-motion rules remain effective.

## 5. Status, Market, and Dashboard Identity

- [x] 5.1 Migrate FeedbackMessage, load/ready/error states, status pills, and operation summaries to `--status-*`; empty/neutral states use text/border roles. Preserve component-local state bindings only as selectors of canonical tokens; verify no feedback consumer references interaction or market tokens.
- [x] 5.2 Migrate positive, negative, and neutral return styling to `--market-up`, `--market-down`, and `--market-flat`; verify China-market red-up/green-down behavior and textual/sign cues remain intact.
- [x] 5.3 Remove the unlabeled Dashboard category-color function/inline palette mapping and render its hairline as a neutral structural marker; verify Dashboard behavior/data tests remain unchanged and no replacement category palette is added.

## 6. Chart Palette and Stable Mapping

- [x] 6.1 Update `seriesColor.ts` to return `--chart-series-1..6` while preserving explicit supported-key mapping and deterministic reserved-role hashing; verify the focused series-color tests pass.
- [x] 6.2 Migrate equity and rolling-stability series, grid, axes, crosshair, labels, swatches, and highlight marks to chart roles without changing geometry/tick/collision logic; verify chart unit/component tests and textual legends remain intact.
- [x] 6.3 Migrate ETF trend and stitched OOS single-series lines/highlights to `--chart-primary-line` or the matching chart identity; verify their tests no longer expect interaction/acid-lime tokens and geometry source remains behaviorally unchanged.

## 7. Command Palette and Readable Active States

- [x] 7.1 Migrate the Command Palette dialog, input, rows, text, metadata, and error state to raised/panel/hover, text, font, and status roles; verify keyboard, focus trap, filtering, selection, and `aria-activedescendant` tests remain green.
- [x] 7.2 Promote readable metadata from tertiary to secondary on hover/active surfaces and add a concentrated contrast/static assertion; verify the active-row foreground/background pair meets WCAG AA normal-text contrast.

## 8. Static Enforcement and Documentation

- [x] 8.1 Replace the acid-lime Stylelint restriction with maintainable checks for removed tokens/literal component palette colors while preserving existing button, line-height, and radius guards. Reuse the separate `npm --prefix apps/web run lint:css:root` command and add a concentrated canonical-full-path root assertion; verify invalid fixtures fail and conforming production CSS passes.
- [x] 8.2 Run the required legacy color and font searches over runtime CSS/TS/TSX, including inline old token strings; verify zero legacy runtime declarations or consumers remain under `apps/web/src/`. Negative-test fixtures may contain old names only to prove rejection and must remain outside production bundles.
- [x] 8.3 Add the narrow `.gitignore` exception needed to track only `docs/tokens.md`, regenerate it with `npm --prefix apps/web run build:tokens-doc`, and verify it lists every canonical semantic group/value and appears in `git ls-files` once staged by the delivery workflow.
- [x] 8.4 Update affected Ladle stories or visual-contract tests only where the new semantic states require coverage; verify stories still render production components and do not enter the production bundle.

## 9. Visual, Responsive, and Accessibility Review

- [x] 9.1 Review AppShell, Dashboard, Signals/Backtests/Walk-forwards list/detail pages, ETF detail, and Command Palette in a real browser with intercepted API fixtures or existing stories covering loading/error/empty/success. Do not invoke real data-mutating actions or a database-backed API. Verify semantic colors, both actual Geist faces, Chinese/Latin and symbol fallback, and record route/state/fixture/evidence locations.
- [x] 9.2 Review shared layouts at 1440x1000, 1280x900, 390x844 and widths 1025/1024/1023, 901/900/899, 721/720/719; review representative dense content/dialogs at wide/narrow sizes. Verify heading/nav wrapping, metric cards, Mono overflow, table containment, chart end labels, compact-list baselines, and mobile buttons; retain screenshot/evidence locations.
- [x] 9.3 Verify normal-text contrast, visible `focus-visible`, textual chart legends, non-color market cues, `aria-pressed`, `aria-current`, skip-link/main focus, and reduced motion; record any accepted limitation before completion rather than weakening a test.

## 10. Completion Gates

- [x] 10.1 Run focused token/font/chart/AppShell/Command Palette tests and `npm --prefix apps/web run build:tokens-doc`; verify all changed contracts pass before the broad gate.
- [x] 10.2 Run `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and `npm --prefix apps/web run build`; verify all five Web CI-equivalent commands pass without running `npm ci` unless dependency files changed or `node_modules` is untrusted.
- [x] 10.3 Run the required complete Python gate after font-test/script changes: `uv sync --group dev`, `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, and `uv run --no-sync pytest`; verify all pass using test-owned temporary data. Also run `npm --prefix apps/web run lint:css:root` explicitly.
- [x] 10.4 Run `openspec validate redesign-web-visual-system --strict`, `openspec validate --all --strict`, `openspec doctor`, and `git diff --check`; compare any broad validation failures with the pre-change baseline and verify this Change introduces none.
- [x] 10.5 Inspect the final diff and file inventory; verify only Change-owned Web/design-system files and font tests/tooling changed, backend/data/chart-geometry behavior is untouched, `vela.db` is unchanged, and all unrelated user work remains preserved.
