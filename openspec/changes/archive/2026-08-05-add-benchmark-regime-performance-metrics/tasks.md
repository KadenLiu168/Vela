## 1. Preconditions and pure metric contract

- [x] 1.1 Confirm `add-stitched-oos-equity-curve` is complete or archived, re-check the current worktree and main specs, and preserve all unrelated changes and `vela.db`.
- [x] 1.2 Add failing independent-oracle tests for CSI 300 proxy Alpha/Beta/R-squared, 252-session compounded Alpha, public six-place precision, and observation count.
- [x] 1.3 Add failing independent-oracle capture tests that compound aligned daily returns into chronological calendar-month buckets, classify positive/negative/zero regimes from benchmark monthly returns, calculate geometric-mean ratios without annualization, and cover both fixed benchmark keys, selected-month counts, partial edge months, near-zero but non-zero denominators, and empty-regime behavior.
- [x] 1.4 Add failing boundary tests for date/order mismatch, fewer than two CAPM observations, zero proxy variance, constant strategy variance, invalid daily/monthly returns, empty monthly regimes, and equal-weight null CAPM fields with independently available monthly capture.
- [x] 1.5 Implement the smallest immutable public `BenchmarkRegimeMetrics` calculation path and exports that satisfy the pure tests without intersecting, filling, sorting, or prematurely quantizing inputs.

## 2. Persistence and atomic execution

- [x] 2.1 Add a single Alembic revision plus ORM fields for nullable benchmark-owned CAPM/capture values and counts, with file-backed SQLite upgrade/downgrade and legacy-preservation tests.
- [x] 2.2 Extend benchmark result calculation and persistence with failing fresh-session round-trip tests proving correct benchmark ownership, null equal-weight CAPM, and unchanged existing fields.
- [x] 2.3 Integrate the metric family into normal success/partial and selected OOS execution, record `benchmark_regime_metrics_v1`, and prove benchmark-skipping training trials remain unchanged.
- [x] 2.4 Add transaction regressions proving any regime-calculation or late persistence failure rolls back signals, run, curves, benchmarks, existing metrics, and new metrics together.
- [x] 2.5 Extend human-readable backtest reports with exact persisted proxy/monthly-capture values, selected-month counts, semantic labels, and legacy null output tests.

## 3. Walk-forward evidence and history

- [x] 3.1 Add failing report tests for per-window proxy/monthly-capture values and metric-local aggregates, including selected-month count units, null exclusion, valid zero values, differing valid counts, and no verdict.
- [x] 3.2 Implement `wf_evidence_v2` generation and terminal reporting while preserving all v1 evidence meanings and avoiding stitched-curve recalculation.
- [x] 3.3 Extend persistence/query validators to strictly round-trip v2 and continue reading v1; add corruption tests for version, ownership, benchmark keys, counts, values, and source-row mismatch.
- [x] 3.4 Add temporary-database Walk-forward integration coverage proving selected OOS rows, v2 evidence, caller-owned atomicity, and legacy v1 readability.

## 4. Typed HTTP contracts

- [x] 4.1 Add failing schema/router/OpenAPI tests for required nullable benchmark fields, daily CAPM versus selected-month capture count semantics, six-place Decimal strings, CSI-only CAPM ownership, and unchanged legacy/list behavior.
- [x] 4.2 Extend backtest response models and serializers to return stored values without financial recomputation.
- [x] 4.3 Add failing Walk-forward API tests for validated v2 per-window/aggregate evidence with selected-month capture counts, legacy v1 detail, strategy scoping, and no partial response for corrupt evidence.
- [x] 4.4 Extend Walk-forward response models and serializers while preserving existing stitched-OOS and other evidence fields.

## 5. Web presentation

- [x] 5.1 Extend client types/fixtures and add failing Backtest Detail tests for proxy-qualified Alpha, Beta, R-squared, both monthly-capture groups, selected-month counts, semantic formatting, and legacy/undefined placeholders.
- [x] 5.2 Implement the smallest benchmark-group presentation changes without adding browser-side calculations, thresholds, scores, or Dashboard/list content.
- [x] 5.3 Add failing Walk-forward Detail tests for per-window and aggregate v2 evidence, monthly-capture labels, selected-month count units, metric-local statuses/counts, legacy v1 behavior, and preservation of stitched and existing evidence.
- [x] 5.4 Implement the Walk-forward evidence presentation with semantic headings, benchmark ownership, keyboard access, and no fabricated null values.
- [x] 5.5 Add deterministic rendered-browser coverage at 1440x1000 and 390x844 for grouping, readable labels/counts, existing navigation/actions, and absence of page-level horizontal overflow.

## 6. Verification and independent review

- [x] 6.1 Run all focused core, migration, persistence, execution, report, Walk-forward, API, and Web tests after the final implementation revision and repair every related failure without writing to `vela.db`.
- [x] 6.2 Run the complete Python gate: `uv sync --group dev`, `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, and `uv run --no-sync pytest`.
- [x] 6.3 Run the complete Web gate: `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and `npm --prefix apps/web run build`.
- [x] 6.4 Independently trace every requirement through implementation and focused tests; review daily CAPM and monthly geometric-capture formulas, partial edge months, count units, alignment, precision, equal-weight ownership, migration, transaction, evidence-version sequencing into the downstream tail-distribution Change, API, accessibility, and viewport semantics and repair confirmed defects.
- [x] 6.5 Run `openspec validate add-benchmark-regime-performance-metrics --strict`, `openspec validate --all --strict`, and `openspec doctor`; inspect the final scoped diff and confirm no default-database mutation, archive, commit, or push occurred.
