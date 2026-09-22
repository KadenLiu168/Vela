## Context

See `proposal.md` for motivation. The Web frontend is a React/Vite application with one large plain-CSS stylesheet and a single canonical `tokens.css` root. Current living specs and static checks pin a Linear midnight palette, acid-lime interaction identity, an Inter-only runtime, three legacy font aliases, and exact `--color-series-*` values. Those contracts must migrate before implementation can conform.

The visual system is widely consumed: `styles.css` contains dozens of old color and font references; several TSX chart/category paths emit token strings inline; tests assert exact series-token names; `index.html` preloads Inter; and `scripts/fonts/inter/` records the existing subset provenance. AppShell and Command Palette already have the required accessibility structure, so preserve their component trees except for the narrow semantic classes/presentational spans described in decision 4.

## Goals / Non-Goals

**Goals:**

- Establish one dark Celestial Research system whose tokens express meaning rather than color names.
- Load a real Sans/Mono pair and apply it by content semantics.
- Keep interaction, system state, China-market direction, and chart identity disjoint.
- Preserve stable chart keys, accessibility behavior, responsive behavior, and existing product logic.
- Make the migration mechanically auditable through concentrated token/static tests, grep checks, generated documentation, and the full Web gate.

**Non-Goals:**

- No light theme, information-architecture change, routing/API/backend change, chart-geometry change, dashboard data change, spacing/radius redesign, fourth button variant, UI framework, or broad React component rewrite.
- No independent motion cleanup. Only selectors touched by this change replace literal transition values with the existing motion vocabulary.
- No new categorical product palette for the Dashboard ETF hairline.

## Decisions

### 1. Use direct semantic roles as the runtime API

`tokens.css` remains the only runtime source. Components consume these families:

```text
surface-*      canvas, panel, raised, hover
border-*       subtle, strong
text-*         primary, secondary, tertiary
interactive-* primary, hover, pressed
status-*       success, warning, danger, info
market-*       up, down, flat
chart-*        primary-line, grid, axis, crosshair, series-1..6
font-*         sans, mono
```

The exact values are contract-owned in the design-system delta. Existing structural families such as spacing, radius, motion, layout, and card aliases remain, but card aliases rebase onto the new semantic surfaces/borders. Legacy palette aliases are not retained after migration because they would let consumers continue conflating meanings.

Alternative considered: keep the old palette primitives underneath semantic aliases. Rejected because the requested done definition requires legacy declarations and consumers to disappear, and keeping color-name primitives would preserve an attractive nuisance.

### 2. Pin official Geist v1.7.2 WOFF2 files without adding npm dependencies

Vendor the official release resources under stable repository filenames:

```text
apps/web/public/fonts/Geist-Variable.woff2
apps/web/public/fonts/GeistMono-Variable.woff2
```

Record upstream tag/URLs, SHA-256 values, and `OFL-1.1.txt` under `scripts/fonts/geist/`. The inspected files are approximately 68 KiB and 70 KiB, expose only `wght 100–900`, and have family names `Geist` and `Geist Mono`; CSS declares the product-facing families `Geist Sans` and `Geist Mono`. Two `@font-face` rules and two matching preloads replace the Inter rule/preload. Remove the served Inter subset and `scripts/fonts/inter/` inputs only after the replacement files and license are verified.

The existing Inter feature token is removed: Geist does not expose the same `opsz`, `cv01`, or `zero` contract. Quantitative alignment relies on Geist Mono plus `font-variant-numeric: tabular-nums`; any optional Geist feature use must be supported by both the actual file and a semantic need.

The official release is `https://github.com/vercel/geist-font/releases/tag/v1.7.2`. Before removing Inter, verify the exact downloaded binaries against the spec hashes and record their precise download URLs or archive member paths. Release-page availability alone does not prove binary hashes. Replace `tests/test_inter_font.py` with font-contract tests using the already-installed FontTools: verify both hashes, WOFF2 format, family names, upright weight axes, OFL notice, preload/font-face URLs, and asset inventory. Retain coverage of Latin text, digits, punctuation, minus, arrows, and UI symbols; unsupported glyphs and Chinese text must render through the documented system fallback instead of tofu. Do not carry over Inter-only subset reproduction, excluded repertoires, or feature assertions. Preserve `font-display: swap`, avoid an obsolete Inter `unicode-range`, and update the font instructions in `scripts/README.md`. This necessarily triggers the complete Python gate as well as the Web gate; no dependency cleanup is needed.

Alternative considered: install the `geist` npm package. Rejected because the application is not Next.js, runtime files are already self-hosted, and adding a dependency would weaken exact binary provenance without simplifying the CSS path.

### 3. Replace the scale by semantic research roles

Use exact role pairs rather than preserve the 48/64/72 display ladder:

| Role | Size / line height | Family | Approx. weight |
|---|---|---|---:|
| Page title | 36 / 40px | Sans | 580 |
| Section title | 22 / 28px | Sans | 580 |
| Card title | 16 / 22px | Sans | 560 |
| Metric hero | 32 / 36px | Mono | 520 |
| Metric | 24 / 30px | Mono | 520 |
| Body | 15 / 22px | Sans | 400 |
| Dense/table | 13 / 20px | role-dependent | 400 |
| Label | 12 / 16px | Sans | 560 |
| Meta | 11 / 16px | role-dependent | 520 |
| Chart axis | 11 / 16px | Mono | 450 |

Every line height remains a named `--leading-*` token. The existing four-rung card data ladder becomes meta 11/16, body 13/20, emphasis 24/30, and display 32/36; card titles use the separate 16/22 title role. This preserves the useful card-role contract without forcing titles into the data ladder.

The AppShell brand uses Sans at 22/28px, weight 620, tracking `-0.035em`, and remains non-heading text below the 36px route heading.

Compact-list labels are an explicit row-layout exception: retain 11px Sans labels and 13px role-dependent values, but bind both `dt` and `dd` to `--leading-body-card: 20px` and align their text baselines. Standalone meta remains 11/16. Retain `--tracking-meta: 0.06em` and `--tracking-numeral: -0.01em` as required by the unchanged tracking contract.

### 4. Migrate consumers systematically by semantic family

Implement in dependency order:

1. Add the final tokens and rebase shared aliases.
2. Replace global body/focus/AppShell rules.
3. Replace surfaces, borders, text, and buttons throughout `styles.css`.
4. Assign Sans/Mono by content semantics, preserving tabular numerals.
5. Replace feedback and market-direction consumers.
6. Replace chart CSS and inline TSX token strings.
7. Remove legacy declarations only after consumer grep is empty.

This makes each token family auditable; intermediate commits may be visually incomplete, so acceptance applies to the completed migration. JSX changes are limited to removing the Dashboard category-color function/inline style, changing inline chart tokens, or adding narrow semantic classes/wrappers to distinguish data from language in tables, description lists, forms, and Command Palette values. Reuse existing elements; where a single text node combines an ETF symbol or date with a name, a presentational span is allowed. Keep accessible names, DOM order, event handling, and public component behavior intact. Do not infer font role from whether a formatted string looks numeric or use table-wide Mono styling.

### 5. Keep status, market, interaction, and chart flows disjoint

```text
user action/focus ───────────────▶ interactive-*
operation outcome/load state ────▶ status-*
positive/negative/flat return ───▶ market-*
series/grid/axis/crosshair ──────▶ chart-*
```

`--feedback-accent-*` may be used briefly as aliases to status roles while selectors migrate, but final source consumers should prefer `--status-*`; unused aliases are deleted. Loading uses `status-info`, ready/success uses `status-success`, errors use `status-danger`, and empty/neutral surfaces use readable text/border roles rather than borrowing a market or interaction color.

Existing component-local `--status-accent` is a state binding, not a new palette: it may select a canonical status token (or a neutral border token for empty state). All actual palette declarations remain in `tokens.css`. Readable market figures and chart labels may use their corresponding semantic colors when contrast passes; they are exceptions to the general text-token rule.

The current Dashboard ETF category hairline is neutralized to a border/text structural role. Keeping category hue would require a labeled domain palette and accessibility contract, which is not justified for this redesign.

### 6. Preserve stable chart identity, not old token names

`seriesColor.ts` keeps its explicit mapping and deterministic reserved-key hash. Only returned token names change:

```text
strategy             -> --chart-series-1
equal_weight_monthly -> --chart-series-2
csi_300_buy_hold     -> --chart-series-3
unknown              -> deterministic --chart-series-4..6
```

Equity/rolling charts retain legends, direct labels, tick generation, collision handling, and geometry. ETF trend and stitched OOS single-series lines/highlights use `--chart-primary-line` or the corresponding series identity, never `--interactive-primary`. Grid, axis, and crosshair use their chart primitives.

### 7. Treat contrast by rendered state, not token in isolation

The proposed palette meets AA for normal text on canvas, panel, and raised surfaces. `--text-tertiary` on `--surface-hover` is approximately 4.41:1, so active/hover rows promote readable metadata to `--text-secondary`; decorative tertiary marks may remain when they carry no text meaning. Chart direct-label colors meet AA on raised surfaces, and text legends remain mandatory so hue is not the only identity cue.

Focus continues to use a 2px visible outline with offset. Nav `aria-current`, button `aria-pressed`, skip-link focus, main programmatic focus, dialog trapping, `aria-activedescendant`, and reduced-motion behavior remain behaviorally unchanged.

### 8. Keep generated token documentation derived and tracked

Run the existing zero-dependency generator after tokens settle. Because `.gitignore` currently excludes all of `docs/` while the living spec requires `docs/tokens.md` to be committed, add the narrowest ignore exception that tracks only `docs/tokens.md`; do not expose other local documents. Validate that every canonical token appears and aliases resolve.

### 9. Concentrate exact-value tests

Exact palette/font contracts belong in static token/font tests and OpenSpec, not component tests. Update `seriesColor.test.ts` to assert the six chart tokens, exact values, and stable key behavior. Component tests continue to assert semantic classes, token role strings where the component itself emits them, and accessibility behavior. Add static checks for font files/preloads, legacy-token absence, and canonical token grouping if no equivalent test exists.

Visual review covers AppShell, Dashboard, list/detail tables, charts, feedback states, and Command Palette at desktop plus the existing 1024/900/720 breakpoints. Mono width is specifically checked for symbols, dates, metrics, table minimum widths, chart end labels, and mobile buttons.

Use deterministic intercepted API fixtures or existing stories without starting the database-backed API or invoking real Bootstrap/signal/backtest actions. Include Dashboard, Signals, Backtests, Walk-forwards list/detail, ETF detail, and loading/error/empty/success states. Capture browser evidence at 1440x1000, 1280x900, 390x844, and widths 1025/1024/1023, 901/900/899, and 721/720/719. Check the shared shell at every boundary and representative dense pages/dialogs at narrow and wide sizes; do not require a full route-by-width Cartesian suite. Confirm actual font loading, mixed Chinese/Latin and UI-symbol fallback, baseline alignment, overflow, active metadata contrast, and keyboard behavior. Record fixture, route, viewport, result, and screenshot/evidence location.

`lint:css` does not currently invoke the separate `lint:css:root` guard. Reuse `npm --prefix apps/web run lint:css:root` explicitly in focused/final checks and add a concentrated full-path canonical-root assertion with the static tests; do not assume Stylelint already enforces it. Legacy-absence checks inspect runtime declarations/references in CSS/TS/TSX, not negative-test fixtures that intentionally name forbidden tokens. Keep those fixtures available so the guard can prove rejection. The generated documentation must be current and unignored during Apply; `git ls-files` becomes a delivery check only after explicit staging authorization.

The two existing `research-workbench-ui` requirements mentioning acid-lime also migrate in this Change; their action-selection and accessibility rules remain verbatim. The standalone `apps/web/public/favicon.svg` is outside this source-token migration and retains its existing artwork; no icon redesign is included.

## Risks / Trade-offs

- [Two font files increase initial font transfer] → Both files are small official variable WOFF2s and both are used above the fold; verify build output and avoid static/italic duplicates.
- [Changing font metrics creates overflow or label collisions] → Preserve geometry algorithms, review required breakpoints, and test table/chart containment rather than altering math to hide typography issues.
- [Large CSS replacement causes semantic misclassification] → Migrate by token family, use grep/static tests, and inspect representative component groups before removing legacy tokens.
- [`text-tertiary` misses AA on hover] → Promote readable active-row metadata to `text-secondary` and encode that rule in specs/tests.
- [Generated local `docs/tokens.md` is stale and ignored] → Regenerate from the canonical source and add only a file-specific tracking exception.
- [Existing design-system requirements overlap card-type-scale] → Update both capability deltas in the same Change and validate the named Change plus broader spec health before Apply is considered complete.
- [Official upstream release may change later] → Pin v1.7.2 URLs and hashes; a future upgrade requires its own reviewed contract change.

## Migration Plan

1. Validate all five delta specs before touching runtime code.
2. Vendor and verify Geist Sans/Mono plus the OFL/provenance record; add matching `@font-face` and preload declarations.
3. Introduce the complete semantic token system and research type roles in `tokens.css`.
4. Migrate `styles.css` consumers by surface/border/text, typography, interaction, status/market, then chart families; replace touched literal transitions with motion tokens.
5. Update the narrow inline TSX/chart consumers and stable series-token resolver without changing component behavior or geometry.
6. Update concentrated static/series tests, Stylelint rules, stories only where visual states require coverage, and regenerate the tracked token reference.
7. Run legacy-token/font greps, targeted tests, the separate root guard, named strict validation, broader OpenSpec checks, visual/responsive review, then the complete Web and Python CI-equivalent gates.
8. Keep the Change active for independent verification. Sync/archive/commit/push remain separate actions requiring their normal workflow and authorization.

Rollback is file-level: restore the previous CSS/tokens/font resources and matching tests/spec delta before archive. No data migration or persistent-state rollback is involved.
