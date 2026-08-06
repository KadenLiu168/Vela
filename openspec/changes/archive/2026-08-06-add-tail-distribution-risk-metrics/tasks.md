## 1. Preconditions and pure distribution contract

- [x] 1.1 Confirm `add-benchmark-regime-performance-metrics` is complete or archived with `wf_evidence_v2`, rebaseline any completed return-stability work, and preserve unrelated changes and `vela.db`.
- [x] 1.2 Add failing tests for the 99/100-observation boundary, exact `ceil(5%)` tail counts, null metric publication below threshold, and independence from the existing three-window WF evidence threshold.
- [x] 1.3 Add a failing 100-return independent oracle for nearest-rank positive-loss Historical VaR 95% and exact-cardinality Historical CVaR 95%, including six-place precision and `CVaR >= VaR >= 0`.
- [x] 1.4 Add failing bias-corrected Fisher-Pearson Skewness and Fisher excess Kurtosis oracle tests plus constant-distribution null-shape and all-non-negative zero-loss boundaries.
- [x] 1.5 Implement the smallest immutable public `TailDistributionRiskMetrics` calculation path and exports, retaining unquantized intermediates and explicit counts/status without adding a new risk dependency.

## 2. Persistence and atomic execution

- [x] 2.1 Add one Alembic revision and nullable ORM fields for strategy/benchmark distribution values and counts, with file-backed SQLite upgrade/downgrade and legacy-preservation tests.
- [x] 2.2 Extend strategy and benchmark calculation/result paths with failing ownership tests proving identical returns yield identical absolute metrics and existing relative/summary metrics remain unchanged.
- [x] 2.3 Extend persistence/query helpers with fresh-session round-trip tests for sufficient metrics, insufficient null metrics with non-null counts, constant shape nulls, and legacy all-null fields.
- [x] 2.4 Integrate `tail_distribution_metrics_v1` into normal success/partial, selected OOS, and isolated training calculation snapshots while retaining benchmark-skipping/source-database isolation.
- [x] 2.5 Add transaction regressions proving any distribution calculation/validation/persistence failure rolls back signals, runs, curves, benchmarks, existing metrics, and new metrics together.
- [x] 2.6 Extend human-readable backtest reports with exact stored values, confidence/horizon/sign/baseline semantics, counts/status, the insufficient-sample tail-cardinality explanation, and legacy/undefined output tests.

## 3. Walk-forward evidence v3

- [x] 3.1 Add failing report tests for per-window strategy/equal-weight/CSI 300 distribution values, counts, statuses, null/zero handling, and stitched-OOS exclusion.
- [x] 3.2 Add failing aggregation tests for each owner/metric's mean/median/min/max/population standard deviation, total/valid counts, evidence status, explicit cross-window descriptive semantics, and absence of combined-distribution, universal best/worst, or pass/fail labels.
- [x] 3.3 Implement `wf_evidence_v3` as a strict extension of v2 and update terminal reporting without mutating established v1/v2 meanings.
- [x] 3.4 Extend persistence/query validators to support valid v1/v2 and strict v3; add corruption tests for versions, owners, benchmark keys, counts, non-finite values, loss invariants, and referenced OOS mismatch.
- [x] 3.5 Add temporary-database Walk-forward integration coverage proving selected OOS source ownership, v3 round-trip, caller-owned atomicity, and legacy v1/v2 readability.

## 4. Typed HTTP contracts

- [x] 4.1 Add failing backtest schema/router/OpenAPI tests for nullable six-place distribution values, nullable legacy/non-null new counts, derived evidence statuses, positive-loss invariants, and strategy/benchmark ownership.
- [x] 4.2 Extend backtest run/detail serializers to expose stored metrics and count-derived statuses without sorting returns or recalculating financial values.
- [x] 4.3 Add failing Walk-forward schema/router/OpenAPI tests for v3 per-window/aggregate groups, named owners, metric-local counts/statuses, valid v1/v2 compatibility, and no partial corrupt-v3 response.
- [x] 4.4 Extend Walk-forward serializers while preserving benchmark-regime, stitched-OOS, and all existing evidence fields.

## 5. Web presentation

- [x] 5.1 Extend client types and deterministic fixtures for sufficient, insufficient, legacy, constant-shape, and valid-zero-loss strategy/benchmark states plus v1/v2/v3 Walk-forward histories.
- [x] 5.2 Add failing Backtest Detail tests for exact API values, one-day historical positive-loss labels, 95% confidence, counts/status, excess-kurtosis normal-zero baseline, owner grouping, distinct null explanations, and the 99-observation/five-tail-count publication-threshold explanation.
- [x] 5.3 Implement the smallest strategy/benchmark distribution presentation without browser arithmetic, regulatory/forecast language, thresholds, scores, or Dashboard/list content.
- [x] 5.4 Add failing Walk-forward Detail tests for per-window/aggregate v3 owner/metric evidence, mixed valid counts, null/zero behavior, explicit cross-window rather than combined-distribution interpretation, v1/v2 compatibility, and preservation of benchmark-regime/stitched/navigation content.
- [x] 5.5 Implement v3 distribution evidence presentation with semantic headings, exact counts/statuses, the cross-window descriptive explanation, keyboard access, and no combined-distribution, universal best/worst, or pass/fail claim.
- [x] 5.6 Add deterministic rendered-browser coverage at 1440x1000 and 390x844 for grouping, labels, counts/nulls, existing actions, and absence of page-level horizontal overflow.

## 6. Verification and independent review

- [x] 6.1 Run all focused numerical, migration, persistence, execution, report, Walk-forward, API, component, and rendered-browser tests after the final revision and repair every related failure without writing to `vela.db`.
- [x] 6.2 Run the complete Python gate: `uv sync --group dev`, `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, and `uv run --no-sync pytest`.
- [x] 6.3 Run the complete Web gate: `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and `npm --prefix apps/web run build`.
- [x] 6.4 Independently trace every requirement through implementation/tests; review threshold, rank/tail, sign, shape correction, precision, ownership, migration, transaction, v3 compatibility, API, accessibility, and viewport semantics and repair confirmed defects.
- [x] 6.5 Run `openspec validate add-tail-distribution-risk-metrics --strict`, `openspec validate --all --strict`, and `openspec doctor`; inspect the final scoped diff and confirm no default-database mutation, archive, commit, or push occurred.
