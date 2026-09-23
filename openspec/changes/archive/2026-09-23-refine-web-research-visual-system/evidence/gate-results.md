# Verification record — Web gate + evidence index (task 5.5 / 5.6)

Executed 2026-09-23, git HEAD `3eafd31e` (+ working tree = this change),
`VITE_API_BASE_URL` cleared for `test`, build and acceptance runs.

| Gate | Command | Result |
| --- | --- | --- |
| lint | `npm --prefix apps/web run lint` | pass (exit 0) |
| lint:css | `npm --prefix apps/web run lint:css` | pass (exit 0) |
| lint:css:root | `npm --prefix apps/web run lint:css:root` | pass — "no `:root` block outside tokens.css" |
| typecheck | `npm --prefix apps/web run typecheck` (`tsc -b`) | pass (exit 0) |
| test | `npm --prefix apps/web run test` (env cleaned) | pass — 43 files, 514 passed / 7 skipped |
| build | `npm --prefix apps/web run build` (env cleaned) | pass (exit 0) |
| ladle:build | `npm --prefix apps/web run ladle:build` | pass (0.63 MiB; catalog absent from production `dist/`) |
| build:tokens-doc | `npm --prefix apps/web run build:tokens-doc` (run twice) | pass — second run byte-identical (md5 `d266613f463b2cb9cffa941c4ca18a03`) |
| test:e2e | `npm --prefix apps/web run test:e2e` | pass — 143 passed, 4 skipped (baseline gated); rerun after Stage 3 repairs |

Note: `test:integration:api` is an opt-in script that requires a real local
FastAPI service; per design.md it is NOT part of this Change's gates and must
not run against a real backend here. `npm test` skips it when
`VITE_API_BASE_URL` is unset (verified passing).

## Requirement → implementation → evidence index

| Requirement (delta) | Implementation | Evidence |
| --- | --- | --- |
| design-system: semantic layout/control tokens | `tokens.css` group 11/15 (`--section-gap(-compact)`, `--group-gap`, `--heading-content-gap`, `--page-gutter-*`, `--card-padding-*`, `--control-*`), rem migration | `designSystem.test.ts` 27/27; `e2e/specs/tokens.spec.ts`; `e2e/specs/spacing.spec.ts`; `e2e/specs/responsive.spec.ts` |
| design-system: type scale + compact page title | tokens.css roles + ≤720px media rule | `typography.spec.ts` (cross-page 36/40, 28/36); `matrix.spec.ts` breakpoint edge checks |
| design-system: panel surface roles / no shadow / palette elevation | `.dashboard-panel`→`--panel-bg`; `.metric`/`.research-headline`→raised; `--card-shadow: none`; palette keeps `--shadow-xl` | `e2e/specs/surfaces.spec.ts` |
| design-system: control states / sizes / pending width / error association | `--control-min-height/--control-touch-size` wiring, pointer:coarse block, bootstrap pending label, aria-invalid/aria-describedby | `controls.spec.ts`; `DashboardPage.test.tsx` (association + pending width); designSystem coarse-pointer test |
| design-system: motion vocabulary + reduced motion | 120ms hover tokens, universal reduced-motion zeroing incl. pseudo-elements, static skeleton | `motion.spec.ts`; designSystem line-height/motion rules |
| card-type-scale: important date/count ≥12/16, status/risk ≥13/20, compact-list 11/20+13/20 | `.dashboard-load-state`, `.status-pill`, `.research-oos-meta`, `.research-headline-difference`, `.research-fact-lag` → dense; `.etf-row-date` → label | `typography.spec.ts`; `designSystem.test.ts` |
| detail-page-typography-consistency: shared heading roles, stale token removal | single `.page-heading h1` rule + compact media rule | `typography.spec.ts` (9 pages × 2 viewports) |
| web-frontend-app: research order retention | DOM order untouched (verified in baseline inventory + unit region-order tests) | `baseline-inventory.md`; `matrix.spec.ts` populated entries |
| web-frontend-app: narrow-screen completeness | gutters/columns/overflow at 320–1440, keyboard-scrollable regions | `responsive.spec.ts`; `reflow.spec.ts`; `tables-charts.spec.ts` |
| web-frontend-app: AA target | axe scans (9 routes × 2 viewports) clean of all A/AA violations; product focus style and computed contrast ratio checked | `a11y.spec.ts`; `surfaces.spec.ts` |
| web-frontend-app: reproducible isolated acceptance | `e2e/runner.mjs` + context-level interception + SW isolation + fail-closed guard; generated evidence excluded from source identity | `isolation.spec.ts`; `identity.spec.ts`; `e2e/README.md`; `matrix-report.json` |
| charts: stable line styles + synced legend | `seriesLineStyle()` + SVG swatches | `tables-charts.spec.ts`; `seriesColor.test.ts` |

## Scope note

- Mobile-device manual acceptance (real-device software keyboard, VoiceOver
  manual steps) was removed from scope by user decision; narrow-viewport,
  keyboard and contrast coverage is automated (see `a11y.spec.ts`,
  `viewport.spec.ts`, `reflow.spec.ts`, `surfaces.spec.ts`).

## Stage 3 repair verification

After the review repairs, the full Web gate passed again: lint, lint:css,
typecheck, test (514 passed / 7 skipped), and build. The extra lint:css:root
check passed; the unchanged Ladle stories had passed ladle:build in the review.
The full browser run passed 143 / 143 active tests, with 4 baseline-only tests
skipped. The matrix report records the final outcome of the full Playwright run
(143 passed / 4 skipped), 59 passing matrix tests, and 57 screenshots; every
screenshot exists and matches its SHA-256. The recorded source fingerprint
(154 frontend files), harness fingerprint and build manifest hash match fresh
calculations after the report was written. The route/state/viewport
matrix includes Dashboard and three lists in loading/empty/error at desktop and
mobile, plus three Palette states at 1440x1000, 390x844, and 390x400.
