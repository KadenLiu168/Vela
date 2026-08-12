# Tasks: reorganize-backtest-detail

## 1. Pure helpers

- [x] 1.1 Add `resolvePrimaryBenchmark(benchmarks)` pure helper: returns the `csi_300_buy_hold` benchmark when present, otherwise the first benchmark, otherwise `null`; add unit tests for all three branches
- [x] 1.2 Add difference helpers in `backtestFormatters.ts`: `computeMetricDifference(strategyValue, benchmarkValue)` returning `null` when either side is null/non-finite; add unit tests covering null propagation and plain arithmetic
- [x] 1.3 Add `computeVerdict(differences)` pure helper: sign-based `Outperforming` / `Underperforming` / `Mixed` / `null` (withheld) with the ≥2 valid-difference rule; add unit tests for all verdict branches including the withheld boundary
- [x] 1.4 Add human-readable parameter mapping: key→label/format table for `strategy_id`, `config_version`, `type`, `start_date`, `end_date`, `risk_free_rate` (annualized percentage), metric version keys, plus unknown-key raw fallback; add unit tests for known keys, `risk_free_rate` formatting, and unknown keys

## 2. Section components

- [x] 2.1 Create `DecisionSummarySection.tsx`: strategy four headline values + four differences vs Primary Benchmark (CAGR/Total Return from API difference fields, Sharpe/MaxDD via display subtraction) + verdict badge; no-benchmark fallback shows strategy values only
- [x] 2.2 Create `BenchmarkComparisonSection.tsx`: move `ComparisonMatrix` logic in, split into always-visible core table (7 rows: Total return / CAGR / MaxDD / Volatility / Sharpe / Sortino / Calmar) and closed-by-default Advanced Metrics disclosure (drawdown duration/peak/trough/recovery, TE/IR, Up/Down capture + counts, difference rows); reuse `bestCellIndexes`; keep no-benchmark state
- [x] 2.3 Create `DeepAnalysisSection.tsx`: assemble Distribution Risk (strategy + each benchmark), Return Stability, and CSI-300 CAPM sections as three independent closed-by-default disclosures inside a labeled Deep Analysis region
- [x] 2.4 Create `ExperimentConfigSection.tsx`: full run metadata (config version, started/finished at, error message), human-readable parameters via the 1.4 mapping, and closed-by-default Raw Parameters disclosure using the existing `formatParameterSummary`

## 3. Page reordering

- [x] 3.1 Reorganize `BacktestDetailPage.tsx` Overview to the research order: run summary line (Strategy · date range · Status) → DecisionSummarySection → EquityCurveChart (unchanged component) → BenchmarkComparisonSection → DeepAnalysisSection → ExperimentConfigSection
- [x] 3.2 Remove the old hero MetricCard grid, the inline single comparison matrix, the inline three disclosure blocks, the run metadata `<dl>`, and the Parameters `<pre>` block from the page; keep tab state and Signals lazy-loading logic unchanged
- [x] 3.3 Verify Signals tab rendering and pagination behavior are byte-for-byte unchanged in behavior

## 4. Styles

- [x] 4.1 Add minimal `styles.css` classes for the run summary line, Decision Summary region, Deep Analysis region, and Experiment Config key-value list, reusing existing `metric-card`, `disclosure`, and `comparison-matrix` styles where possible; no visual regression to the equity curve chart

## 5. Tests

- [x] 5.1 Migrate existing `BacktestDetailPage.test.tsx` coverage to the new sections: split matrix/disclosure/parameter assertions into per-component test files
- [x] 5.2 Add `DecisionSummarySection.test.tsx`: primary fallback, difference computation (API fields vs display subtraction), verdict badge branches, no-benchmark state
- [x] 5.3 Add `BenchmarkComparisonSection.test.tsx`: core/advanced split, advanced collapsed by default, Best markers, relative rows `n/a` Strategy cell, legacy no-benchmark state
- [x] 5.4 Add `ExperimentConfigSection.test.tsx`: known-key labels/formatting, `risk_free_rate` percent rendering, unknown-key raw fallback, Raw Parameters collapsed content
- [x] 5.5 Keep page-level tests asserting the research-order sequence and run summary line; update any assertions broken by DOM reordering
- [x] 5.6 Add an a11y check for the new disclosure(s) and region labels (keyboard open/close, accessible summary)

## 6. Validation

- [x] 6.1 Run `openspec validate reorganize-backtest-detail --strict`
- [x] 6.2 Run the full Web gate: `npm --prefix apps/web run lint`, `lint:css`, `typecheck`, `test`, `build`
