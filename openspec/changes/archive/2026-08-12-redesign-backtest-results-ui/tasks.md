## 1. Design tokens and stable series identity

- [x] 1.1 Add failing contract/unit tests for the six exact `--color-series-*` token values/catalog entry, WCAG-AA direct-label contrast, and stable distinct mappings for `strategy`, `equal_weight_monthly`, and `csi_300_buy_hold` when another series is absent
- [x] 1.2 Add the six specified categorical tokens only to `apps/web/src/styles/tokens.css` and update its leading catalog comment
- [x] 1.3 Implement the smallest shared `seriesColor(key)` helper with explicit current-key mappings and a deterministic reserved-role fallback; do not change backend benchmark support

## 2. Equity curve chart improvements

- [x] 2.1 Add failing pure geometry tests for shared sorted-date x ticks, numeric y ticks, equal-range values, endpoint coordinates, deterministic three-series label separation, and viewBox bounds
- [x] 2.2 Extend `computeMultiEquityCurveGeometry` and `EQUITY_CURVE_CHART` only as needed to return shared ticks/endpoints while preserving the current shared scale and finite empty/equal-range behavior
- [x] 2.3 Add failing renderer tests for explicit key colors, missing-series identity stability, matching swatches/strokes/end-labels, date/net-value axes, and preserved empty/single-point fallbacks
- [x] 2.4 Implement the equity-curve axes, swatch legend, and bounded direct end-labels using `seriesColor(key)`
- [x] 2.5 Add failing Return Stability tests for the same key colors/legend/end-label behavior, date axes, metric-correct y labels, selector behavior, and preserved exact-value table
- [x] 2.6 Apply the shared geometry/presentation pattern to `ReturnStabilitySection` without mixing Return, Volatility, and Sharpe scales

## 3. Detail page: hero, comparison matrix, progressive disclosure

- [x] 3.1 Add failing component tests for hero order/nullable formatting; exact calendar-time/252D labels; semantic absolute and Strategy-relative row groups; capture counts; legacy no-benchmark state; and no browser-side derivation
- [x] 3.2 Add failing tests for documented best-value directions, ties, null exclusion, minimum-two-value rule, accessible `Best` text, and no ranking on dates/relative/evidence rows
- [x] 3.3 Replace the strategy `MetricCard` grid with the 4-card strategy hero and implement the semantic comparison table with explicit row metadata and owner-correct cells — 方案 A
- [x] 3.4 Implement the accessible comparison highlight rules without changing any financial value
- [x] 3.5 Add failing keyboard/semantics tests for closed-by-default Distribution risk, Return stability, and conditional CSI-300 CAPM disclosures while preserving owner identity, counts/status, null explanations, and exact tables
- [x] 3.6 Move the three secondary groups into native `<details>` disclosures and preserve existing content behavior when expanded

## 4. List page metric columns

- [x] 4.1 Add failing Backtest List component coverage for exact Total return / CAGR (calendar-time) / Sharpe (daily returns, 252D) labels, existing formatter output, null/legacy rows, links, loading/error/empty states, and pagination preservation
- [x] 4.2 Add the three columns using only existing `BacktestListItem` fields (`total_return`, `annualized_return`, `sharpe_ratio`) and existing formatters

## 5. Responsive acceptance and final verification

- [x] 5.1 Add/adjust CSS and component checks proving the matrix/list use labeled keyboard-scrollable local regions, the matrix metric-name column is sticky, and no page-level overflow is introduced
- [x] 5.2 Perform deterministic rendered-browser acceptance for benchmark-enabled detail, legacy/no-benchmark detail, disclosure keyboard operation, and populated/null list rows at 1440×1000 and 390×844; verify chart labels/ticks stay in-bounds and all existing navigation remains usable
- [x] 5.3 Run focused component/geometry tests, then the complete Web gate: `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and `npm --prefix apps/web run build`
- [x] 5.4 Run `npm --prefix apps/web run check:bundle` against the fresh build, then `openspec validate redesign-backtest-results-ui --strict`; inspect the scoped diff and confirm no backend/API/schema/data, `vela.db`, archive, commit, or push mutation occurred
