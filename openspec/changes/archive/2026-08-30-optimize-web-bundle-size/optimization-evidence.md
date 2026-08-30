# Bundle optimization evidence

## Baseline

Captured on 2026-08-29 from `/Users/kaden/Vela` with the existing npm install. `node_modules` contained the expected Vite executable, so the task did not run `npm ci`.

| Identity | Value |
| --- | --- |
| Node | `v25.8.2` |
| npm | `11.11.1` |
| Vite | `7.3.6` |
| Rollup | `4.62.2` |
| `apps/web/package-lock.json` SHA-256 | `770031e7e424b525f90d9da3ea5b7fea06e2e9e67d61b819e9cf50102cd77a34` |

`npm --prefix apps/web run check:bundle` performed a fresh production build and exited `1` for the expected lazy and total budget violations. The reviewed identity and runtime component baselines passed.

| Budget band | Actual raw | Actual gzip | Contract |
| --- | ---: | ---: | --- |
| Required runtime attribution | 229,187 | 73,544 | exact baseline |
| Eager application | 39,965 | 11,238 | <= 40,000 / 12,000 |
| Dashboard initial JavaScript | 269,152 | 84,782 | <= 273,000 / 86,000 |
| Non-initial lazy JavaScript | 77,211 | 22,956 | <= 70,000 |
| Total JavaScript | 346,363 | 107,738 | <= 340,000 raw |

CSS and font measurements are recorded separately: CSS is 51,034 raw / 7,759 gzip bytes and fonts are 86,368 raw / 86,375 gzip bytes. Neither is attributed to route code splitting.

### Initial JavaScript

| Emitted file | Raw bytes | Gzip bytes |
| --- | ---: | ---: |
| `assets/index-PVpUD1iK.js` | 76,805 | 24,570 |
| `assets/react-vendor-C2StAl4u.js` | 192,347 | 60,212 |
| **Initial total** | **269,152** | **84,782** |

### Lazy route entries

| Route source | Emitted file | Raw bytes | Gzip bytes |
| --- | --- | ---: | ---: |
| `src/pages/SignalListPage.tsx` | `assets/SignalListPage-Dza213Gz.js` | 3,555 | 1,465 |
| `src/pages/SignalDetailPage.tsx` | `assets/SignalDetailPage--52We_W9.js` | 3,088 | 1,155 |
| `src/pages/BacktestListPage.tsx` | `assets/BacktestListPage-EjQwP02w.js` | 2,407 | 988 |
| `src/pages/BacktestDetailPage.tsx` | `assets/BacktestDetailPage-C2dxlcPr.js` | 31,827 | 8,054 |
| `src/pages/EtfDetailPage.tsx` | `assets/EtfDetailPage-DWhFd_Le.js` | 5,834 | 2,202 |
| `src/pages/WalkForwardListPage.tsx` | `assets/WalkForwardListPage-BUN6h0SJ.js` | 5,076 | 1,837 |
| `src/pages/WalkForwardDetailPage.tsx` | `assets/WalkForwardDetailPage-JeJ763t0.js` | 22,201 | 5,743 |
| **Route-entry subtotal** |  | **73,988** | **21,444** |

### Non-initial shared JavaScript

| Shared file | Raw bytes | Gzip bytes |
| --- | ---: | ---: |
| `assets/equityCurveChart-CCXGBP7F.js` | 2,812 | 1,223 |
| `assets/Pagination-DxzlMybN.js` | 411 | 289 |
| **Shared subtotal** | **3,223** | **1,512** |
| **Lazy total (route entries + shared, each file once)** | **77,211** | **22,956** |

The same graph reconciles to the complete JavaScript total: `269,152 + 77,211 = 346,363` raw bytes.

The post-reporting fresh `check:bundle` produced the same route files and measurements, the same `269,152` initial raw bytes, `77,211` lazy raw bytes, and `346,363` total raw bytes, then exited `1` only for the two pre-existing budget violations. Reporting did not move or remove emitted bytes.

## Rollup module attribution

The installed Vite/Rollup toolchain was run with a temporary `generateBundle` observer and `write: false`. `renderedLength` is Rollup's per-module rendered attribution before final minified-file measurement; it is diagnostic and is not summed as emitted bytes.

| Route chunk | Rendered module contributors, descending |
| --- | --- |
| Backtest detail (31,827 raw) | `ReturnStabilitySection.tsx` 18,252; `BacktestDetailPage.tsx` 17,838; `BenchmarkComparisonSection.tsx` 9,993; `backtestFormatters.ts` 4,134; `DecisionSummarySection.tsx` 3,870; `DistributionRiskSection.tsx` 3,340; `DeepAnalysisSection.tsx` 2,702; `ExperimentConfigSection.tsx` 2,532; `comparisonMatrix.ts` 720; `seriesColor.ts` 691 |
| Backtest list (2,407 raw) | `BacktestListPage.tsx` 4,524 |
| ETF detail (5,834 raw) | `EtfDetailPage.tsx` 10,388; `etfTrendChart.ts` 1,607 |
| Signal detail (3,088 raw) | `SignalDetailPage.tsx` 6,134 |
| Signal list (3,555 raw) | `SignalListPage.tsx` 6,839 |
| Walk-forward detail (22,201 raw) | `WalkForwardDetailPage.tsx` 31,805; `WalkForwardOosSummarySection.tsx` 4,980; `StitchedOosSection.tsx` 2,655; `walkForwardFormatters.ts` 1,327; `WalkForwardRunHeaderSection.tsx` 1,070 |
| Walk-forward list (5,076 raw) | `WalkForwardListPage.tsx` 9,799 |

### Ranked hypotheses

1. The highest-value candidate is duplicate rendered chart/metric markup in the Backtest detail graph and repeated window metric markup in the Walk-forward detail graph. Keep only a measured net reduction with existing page tests still covering visible, empty, error, and accessibility behavior.
2. `formatDrawdownRecovery` and several formatting patterns are repeated across detail modules, but their emitted contribution is small; a shared helper is only worthwhile if Rollup measures a total reduction without increasing the initial graph.
3. No unused production export was accepted as a deletion hypothesis: the apparently utility-heavy formatter modules have active callers in rendered sections and focused tests.
4. Moving detail code into nested dynamic chunks, eager code, merged route entries, changing minification/dependencies, or raising budgets would only change accounting or identity and is excluded by the Change.

## Optimization iterations

Every retained candidate below was measured with a fresh `npm --prefix apps/web run check:bundle`. Values are cumulative raw-byte totals from that run; the delta is against the original failing baseline. Gzip values were also retained in the final check, but raw bytes are the binding optimization metric.

| Retained candidate | Lazy raw | Total raw | Delta lazy / total |
| --- | ---: | ---: | ---: |
| Baseline | 77,211 | 346,363 | — |
| Walk-forward repeated metric-row reuse | 76,624 | 345,776 | -587 / -587 |
| Shared `EquityCurvePlot` extraction | 75,513 | 344,665 | -1,698 / -1,698 |
| Benchmark comparison table reuse | 75,219 | 344,371 | -1,992 / -1,992 |
| Core metric row descriptors | 74,689 | 343,878 | -2,522 / -2,485 |
| Walk-forward benchmark/capture maps | 74,065 | 343,217 | -3,146 / -3,146 |
| Walk-forward summary/provenance/input maps | 73,143 | 342,295 | -4,068 / -4,068 |
| Tail/count maps and `SimpleMetricGrid` reuse | 73,005 | 342,157 | -4,206 / -4,206 |
| SVG guide paths and shared drawdown formatter | 72,512 | 341,664 | -4,699 / -4,699 |
| Shared table primitives and Backtest table reuse | 70,404 | 339,555 | -6,807 / -6,808 |
| Chart geometry/path helper reuse | 70,138 | 339,289 | -7,073 / -7,074 |
| Final retained set, including chart aliases | **69,995** | **339,146** | **-7,216 / -7,217** |

The intermediate rows combine only adjacent, independently measured reductions that remained in the final source. Small map/table reductions between the displayed checkpoints are included in the next checkpoint; no candidate was retained without a raw-byte reduction. The final retained set did not increase the initial raw band: it is 269,151 bytes versus the 269,152-byte baseline.

Rejected candidates were measured and reverted immediately:

| Candidate | Measured raw delta | Reason for rejection |
| --- | ---: | --- |
| `RELATIVE_METRICS` switch/descriptor rewrite | +79 lazy / +79 total | Increased emitted JavaScript |
| Generic `DecimalMetricRows` / `IntegerMetricRows` wrappers | +27 lazy / +27 total | Increased emitted JavaScript |
| Widening `formatDecimal` to accept numbers | -32 lazy / -24 total, but +8 initial | Violated the no-initial-increase constraint |
| Benchmark evidence consolidation | +39 lazy / +39 total | Increased emitted JavaScript |
| Calendar table-cell class support | +20 lazy / +20 total | Increased emitted JavaScript |
| Run-summary generic metric-card abstraction | +72 lazy / +66 total | Increased emitted JavaScript |
| Aggregated evidence map | 0 lazy / 0 total | No measurable reduction |
| `dateX` chart helper | +33 lazy / +33 total | Increased emitted JavaScript |

## Final fresh bundle check

The final fresh check ran on 2026-08-29 with the same identity and lockfile hash as the baseline and exited `0` with no violations.

| Budget band | Actual raw | Actual gzip | Contract |
| --- | ---: | ---: | --- |
| Required runtime attribution | 229,187 | 73,544 | exact baseline |
| Eager application | 39,964 | 11,223 | <= 40,000 / 12,000 |
| Dashboard initial JavaScript | 269,151 | 84,767 | <= 273,000 / 86,000 |
| Non-initial lazy JavaScript | **69,995** | **23,373** | <= 70,000 |
| Total JavaScript | **339,146** | 108,140 | <= 340,000 raw |

### Final lazy route entries

| Route source | Emitted file | Raw bytes | Gzip bytes |
| --- | --- | ---: | ---: |
| `src/pages/SignalListPage.tsx` | `assets/SignalListPage-Dxh-ix-5.js` | 3,555 | 1,463 |
| `src/pages/SignalDetailPage.tsx` | `assets/SignalDetailPage-C1DGrQIJ.js` | 3,088 | 1,152 |
| `src/pages/BacktestListPage.tsx` | `assets/BacktestListPage-B1GGM8x1.js` | 2,407 | 985 |
| `src/pages/BacktestDetailPage.tsx` | `assets/BacktestDetailPage-CnjDTbx0.js` | 27,381 | 8,286 |
| `src/pages/EtfDetailPage.tsx` | `assets/EtfDetailPage-CtFS7gsz.js` | 5,834 | 2,200 |
| `src/pages/WalkForwardListPage.tsx` | `assets/WalkForwardListPage-Bt4UW_hX.js` | 5,076 | 1,834 |
| `src/pages/WalkForwardDetailPage.tsx` | `assets/WalkForwardDetailPage-CM7pfl4j.js` | 19,124 | 5,730 |
| **Route-entry subtotal** |  | **66,465** | **21,650** |

### Final non-initial shared JavaScript

| Shared file | Raw bytes | Gzip bytes |
| --- | ---: | ---: |
| `assets/Pagination-DxzlMybN.js` | 411 | 289 |
| `assets/tablePrimitives-Cx3EvopJ.js` | 3,119 | 1,434 |
| **Shared subtotal** | **3,530** | **1,723** |
| **Lazy total (each emitted file once)** | **69,995** | **23,373** |

The final graph reconciles exactly: `66,465 + 3,530 = 69,995` lazy raw bytes and `269,151 + 69,995 = 339,146` total raw bytes. The seven page modules remain distinct lazy route entries. The final build identity is Node `v25.8.2`, npm `11.11.1`, Vite `7.3.6`, with unchanged `apps/web/package-lock.json` SHA-256 `770031e7e424b525f90d9da3ea5b7fea06e2e9e67d61b819e9cf50102cd77a34`. No dependency, minifier, budget, route-accounting, nested dynamic import, eager-move, or persistent database change was used.

## Browser regression

The in-app Browser path was attempted first as required by the frontend testing workflow, but the environment returned `No browser is available` and `agent.browsers.list()` returned an empty list. The documented Playwright fallback was used with the existing local wrapper; no browser dependency was added.

The local Vite server was run without starting the backend, so the persistent root `vela.db` was not opened or modified. An initial unmocked Dashboard load confirmed the existing error-recovery UI (`Dashboard API unavailable: http`) when `/api/dashboard` returned 500. For successful content and interaction checks, Playwright mocked only the read endpoints with fixture responses; these mocked requests had no console errors or failed requests.

| Flow | Viewport | Evidence |
| --- | --- | --- |
| Dashboard eager render | 1440x1000 | Page title `Vela Web`, `Dashboard loaded`, populated market/strategy panels, `scrollWidth=1440` |
| Dashboard eager render | 390x844 | Same populated panels, `scrollWidth=390` |
| Dashboard -> Backtests -> `Backtest #7` -> `Signals (1)` | 1440x1000 | Internal navigation reached `/backtests/7`; tab interaction rendered the signal table; no console errors; `scrollWidth=1440` |
| Direct Backtest detail | 390x844 | `/backtests/7` rendered the equity curve and overview; no console errors; `scrollWidth=390` |
| Direct Walk-forward detail | 1440x1000 | `/walk-forwards/42` rendered OOS summary, stitched path, evidence, and provenance; no console errors; `scrollWidth=1440` |
| Direct Walk-forward detail -> history | 390x844 | `/walk-forwards/42` rendered at mobile size; “Back to Walk-forward history” reached the empty history state; no console errors; `scrollWidth=390` |

Screenshots were saved outside the repository at `/tmp/vela-dashboard-desktop.png`, `/tmp/vela-dashboard-mobile.png`, `/tmp/vela-backtest-desktop.png`, `/tmp/vela-backtest-mobile.png`, `/tmp/vela-walk-forward-desktop.png`, and `/tmp/vela-walk-forward-mobile.png`.
