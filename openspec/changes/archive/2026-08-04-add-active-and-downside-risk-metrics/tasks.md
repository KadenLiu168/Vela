## 1. Core metric contracts

- [x] 1.1 Add independently derived fixed-vector tests locking Sortino `45.825757` for annual MAR `0.0252` and returns `[0.0101, -0.0049, 0.0201]`, plus negative excess returns, insufficient observations, zero downside deviation and unquantized intermediates.
- [x] 1.2 Add fixed-value Calmar tests proving the existing published six-decimal CAGR/MaxDD fields are used without curve recomputation, covering negative MaxDD absolute value, negative CAGR, null CAGR and zero drawdown without changing existing metric expectations.
- [x] 1.3 Add longest-drawdown-duration tests covering completed and ongoing intervals, official-session index counts, peak/trough/recovery dates, last-equal-high anchoring, equal-peak recovery, deepest-trough ties, longest-interval ties and never-underwater curves.
- [x] 1.4 Add independently derived TE/IR tests locking `0.038884`/`12.961481` for active returns `[0.002, -0.001, 0.005]`, plus exact date/order alignment, raw-versus-quantized denominator behavior, published-zero TE, zero dispersion and insufficient observations.
- [x] 1.5 Add public-import compatibility tests, then implement and root-export the specified immutable result types and shared calculation functions beside the existing equity-curve metrics without changing existing public signatures.

## 2. Benchmark and runner integration

- [x] 2.1 Add failing benchmark tests requiring pre-signal input/curve construction, shared Sortino/Calmar/duration calculations and post-strategy relative TE/IR without changing either benchmark's existing five metrics or curve.
- [x] 2.2 Extend benchmark results and `run_backtest` with the specified two-phase orchestration: preserve pre-signal benchmark fail-fast, calculate strategy and dual-benchmark expanded metrics after the strategy curve and before result persistence, and record `performance_metrics_v1` plus the exact risk-free rate.
- [x] 2.3 Add runner tests for success and partial normal runs, isolated skipped-benchmark training runs, selected OOS runs, flat curves, metric nulls, pre-signal benchmark failure, late active-metric failure and caller-owned complete rollback without internal commit/rollback.

## 3. Typed persistence and migration

- [x] 3.1 Add nullable expanded-metric fields to the strategy and benchmark ORM models and persistence inputs/outputs, including explicit zero duration for new never-underwater runs.
- [x] 3.2 Create one Alembic revision adding the typed nullable columns to both tables without backfill, with a downgrade that removes only those columns.
- [x] 3.3 Add file-backed Alembic upgrade/downgrade tests proving legacy run, benchmark and curve data survive unchanged with null expanded fields.
- [x] 3.4 Add persistence/query tests proving new strategy and benchmark values round-trip atomically, keep benchmark ordering and remain isolated across reruns.

## 4. Walk-forward evidence extension

- [x] 4.1 After `strengthen-walk-forward-evaluation-contract` is stable, add failing tests for per-window Sortino, Calmar and duration plus separately keyed benchmark TE/IR summaries with metric-local counts/evidence status.
- [x] 4.2 Extend selected-OOS result mapping, aggregation and terminal formatting for the new metrics without adding pass/fail, cross-window path metrics or a continuous OOS curve.
- [x] 4.3 Extend the production-path Walk-forward integration fixture to assert calculated expanded metrics and preserve source transaction rollback behavior.

## 5. API and CLI contracts

- [x] 5.1 Extend FastAPI schemas and response mapping with typed strategy/benchmark expanded fields; add contract and integration tests for decimal strings, integer duration, ISO dates, ongoing recovery and legacy nulls.
- [x] 5.2 Extend `run-backtest` CLI output and exported reports with explicit MAR/252D/calendar-CAGR labels, benchmark-relative TE/IR and ongoing drawdown formatting.
- [x] 5.3 Add CLI regression tests covering new values, unavailable legacy values and unchanged existing five-metric/benchmark output.

## 6. Backtest Detail presentation

- [x] 6.1 Extend Web API types, validation fixtures and client tests for strategy and benchmark expanded metric fields with nullable legacy compatibility.
- [x] 6.2 Add Backtest Detail component tests for semantic labels, benchmark-relative TE/IR ownership, duration dates, ongoing recovery and unavailable legacy values, plus a Dashboard regression proving no expanded field is added there.
- [x] 6.3 Implement the smallest Backtest Detail metric-group extension that satisfies the new contract without changing Dashboard, list pages or the existing three-series curve.
- [x] 6.4 Run browser QA at supported desktop and narrow viewport widths for expanded grouping, semantic labels, duration dates, unavailable values, keyboard navigation, clipping and console errors.

## 7. Validation

- [x] 7.1 Run focused core formula, benchmark, runner, persistence, migration, Walk-forward, API, CLI and Web tests; verify controlled vectors independently from production calculations.
- [x] 7.2 Run `openspec validate add-active-and-downside-risk-metrics --strict` and trace every requirement and scenario to implementation and test evidence.
- [x] 7.3 After the final stable revision, run the complete Python and Web CI-equivalent gates and record results; use only test-owned databases and do not migrate or write default `vela.db`.
