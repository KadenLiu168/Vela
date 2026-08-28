## 1. Pure helpers and formatting

- [x] 1.1 Create `walkForwardFormatters.ts` with `formatPercentNumber(value: number | null, digits = 2)` adapting percentage formatting to `WalkForwardMetricSummary` number inputs (null → `n/a`), covering total return / max drawdown / rate metrics
- [x] 1.2 Implement `resolvePrimaryBenchmark(benchmarks)` picking `csi_300_buy_hold` first, else first benchmark in collection, else null
- [x] 1.3 Implement `aggregateTransitionRate(parameterStability)` returning `{ rate, parameterName, comparisonCount }` for the max per-parameter transition rate, with null-safe handling when no parameter has comparisons; ties resolved by first-in-insertion-order (the backend emits sorted parameter names, making this deterministic)
- [x] 1.4 Implement `generalizationGapText(summary)` producing the IS-minus-OOS-Sharpe explained fact line (ratio format, direction explanation)
- [x] 1.5 Add `walkForwardFormatters.test.ts` covering percent formatting boundaries, primary benchmark fallback, transition max with low-comparison base, transition tie-breaking, and null cases

## 2. Run Header section

- [x] 2.1 Create `WalkForwardRunHeaderSection.tsx` rendering back-link to `/walk-forwards` (with href assertion), `run.status`, and the summary line (Strategy · date range · window count), reusing the backtest detail `.run-summary` / `.run-summary-status` styles; keep the run title in the existing `page-heading` and remove the `panel-primary` "Persisted evaluation evidence" line
- [x] 2.2 Add an Execution metadata subsection (h3) at the top of the provenance region carrying provenance/evidence version and started/finished/created timestamps; `EvidenceSection` and `WindowSection` internals stay unchanged
- [x] 2.3 Add Run Header render assertions in `WalkForwardDetailPage.test.tsx` (first region of the detail body, status, summary line, back-link target); update existing assertions for content that moved into the provenance region

## 3. OOS Summary section

- [x] 3.1 Create `WalkForwardOosSummarySection.tsx` rendering the six headline cards (median/mean return with "median across N windows" annotation, median Sharpe, max drawdown, positive window rate, benchmark outperformance vs primary, parameter transition max with comparison context) using the pure helpers
- [x] 3.2 Render the fact line with Generalization Gap (explained) and Evidence Status sourced from `evidence.metrics.total_return.evidence_status` (≥3 valid windows explanation)
- [x] 3.3 Handle null-evidence state without fabricated values: queued/running keep the existing evidence-unavailable note; failed runs state evidence is unavailable because the run failed
- [x] 3.4 Add `WalkForwardOosSummarySection.test.tsx` covering primary fallback, transition max display, Gen Gap text, queued/running and failed null-evidence states, and percentage/ratio formatting assertions

## 4. Stitched OOS reordering

- [x] 4.1 Extract `StitchedOosSection` from the page into its own component file without changing its content or semantics
- [x] 4.2 Position the stitched section directly after the OOS Summary in the page render order (before Aggregated evidence)

## 5. Page orchestration and deep regions

- [x] 5.1 Slim `WalkForwardDetailPage.tsx` to orchestration: data loading, state machine, and assembly of Run Header, OOS Summary, Stitched section, Aggregated evidence, Window evidence, and Provenance in research order
- [x] 5.2 Keep `EvidenceSection` and `WindowSection` internals unchanged; `ProvenanceSection` only gains the Execution metadata subsection from task 2.2 plus heading-level adjustments as needed
- [x] 5.3 Add page-level ordering assertions to `WalkForwardDetailPage.test.tsx` (Header → OOS Summary → Stitched → Aggregated evidence → Windows → Provenance)

## 6. Styling and verification

- [x] 6.1 Add `styles.css` classes for run-header, oos-summary card grid, and fact line, reusing existing metric-card, holdings-section, and run-summary styles; keep heading typography consistent with the detail-page typography conventions
- [x] 6.2 Run the web test suite and typecheck; confirm existing Walk-forward tests pass and no backend files changed
