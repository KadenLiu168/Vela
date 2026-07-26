## 1. Walk-Forward Configuration

- [x] 1.1 Create `WalkForwardConfig` pydantic model in `walk_forward/config.py` with fields: base strategy config path; window `start_date`, `end_date`, scheme, train/test/step years; non-empty parameter space; `objective: Literal["sharpe_ratio"]`; and optional equal-weight baseline identity
- [x] 1.2 Create `ParameterSpec` discriminated union type supporting `int_range`, `float_range`, `choice` parameter types
- [x] 1.3 Validate unique parameter names, non-empty choices, positive steps, ordered bounds, positive window lengths, ordered analysis dates, and baseline identity fields
- [x] 1.4 Create `load_walk_forward_config(path)` that wraps file/YAML/validation failures consistently and resolves the base strategy path relative to the walk-forward YAML
- [x] 1.5 Create `config/walk_forward_v1.yaml` with `parameters.*` dual-momentum paths, explicit analysis dates, default window settings, Sharpe objective, and a distinct equal-weight baseline identity
- [x] 1.6 Write config-loader tests for valid config plus missing file, malformed YAML, invalid ranges, duplicate paths, invalid dates, unsupported objective, and invalid baseline identity

## 2. Window Splitter

- [x] 2.1 Implement day-clamped calendar-year shifting and `generate_windows(trading_dates, start_date, end_date, train_years, test_years, step_years)` returning inclusive actual-trading-date bounds
- [x] 2.2 Normalize supplied trading dates by sorting/deduplicating; reject insufficient configured range and empty complete intervals; exclude a partial final test interval
- [x] 2.3 Write exact unit tests for three known windows, no train/test overlap, leap-day clamping, insufficient range, weekend/holiday boundary resolution, and partial final exclusion

## 3. Parameter Space & Grid Search

- [x] 3.1 Implement `generate_combinations(parameter_specs)` in `walk_forward/parameter_space.py` producing all value combinations via Cartesian product
- [x] 3.2 Generate `float_range` values with decimal stepping and inclusive reachable high
- [x] 3.3 Implement non-mutating `merge_into_config(base_config_dict, combo)` using full-root dot paths
- [x] 3.4 Implement `build_strategy_config(base_config, combo)` that merges then calls `validate_strategy_config()`, returning a typed result or a structured skip reason
- [x] 3.5 Implement canonical-combination serialization and deterministic Sharpe tie-breaking
- [x] 3.6 Write unit tests for Cartesian products, decimal ranges, non-mutating deep merge, real `parameters.*` paths, unknown paths, valid/invalid strategy combinations, and ties

## 4. Walk-Forward Runner

- [x] 4.1 Implement `WalkForwardRunner` class in `walk_forward/runner.py` with `run(session)` method that orchestrates the full walk-forward
- [x] 4.2 Implement SQLite-only source validation and a single-connection in-memory snapshot factory using SQLite backup before search
- [x] 4.3 Implement training search transactions: build config → run on memory snapshot → commit success or rollback failure → record score/skip reason
- [x] 4.4 Select only successful, non-null Sharpe results; fail before OOS when none are scorable
- [x] 4.5 Generate deterministic behavior-stable `wf-<12 hex>` config versions from canonical validated config content excluding original version, and guard against within-run collisions
- [x] 4.6 Run OOS backtests on the caller's source session with the generated version
- [x] 4.7 Construct an equal-weight baseline from inherited common settings plus explicit distinct identity; run it on test windows and compute nullable annualized-return/Sharpe differences
- [x] 4.8 Handle per-combination ordinary exceptions with memory rollback and warning while leaving process-control exceptions uncaught
- [x] 4.9 Keep source transaction ownership with the caller; do not commit or roll back the caller session inside the runner
- [x] 4.10 Write integration tests with 2 combos/1 window proving input rows exist in the memory snapshot, training rows never reach the source DB, only OOS/baseline rows do, failed combos do not poison later combos, all-invalid search prevents OOS, distinct effective params use distinct versions, and a later failure rolls back all source writes through the CLI boundary

## 5. Report Generation

- [x] 5.1 Implement `WalkForwardReport` dataclass holding exact window boundaries, OOS versions, per-window results/skip reasons, and aggregate statistics
- [x] 5.2 Implement `format_report(report)` producing terminal-readable text with per-window details, OOS aggregate stats, parameter stability, skipped combinations, and nullable baseline comparison
- [x] 5.3 Implement parameter stability analysis: show best value per parameter per window
- [x] 5.4 Write unit tests for mean, median, min, max, population std, one-window std, null OOS/baseline metrics, skip summaries, and complete version-to-parameter rendering

## 6. CLI Command

- [x] 6.1 Add the smallest core public exports and `walk-forward` subcommand wiring to the existing CLI entrypoint
- [x] 6.2 Add required `--config`, optional `--database-url` with the repository default, and optional `--output` arguments
- [x] 6.3 Print the report to stdout or write it to `--output`; handle config file, YAML, validation, non-SQLite, and runtime failures with non-zero exit
- [x] 6.4 Write CLI tests for argument forwarding, default database URL, stdout, output file, missing config, and runtime failure

## 7. Verification

- [x] 7.1 Run focused walk-forward unit/integration/CLI tests, then the repository Python quality gates (`ruff check`, `ruff format --check`, `mypy`, `pytest`)
- [x] 7.2 Copy `vela.db` to a recoverable `/tmp` path and run `vela walk-forward --database-url sqlite+pysqlite:////tmp/<copy>.db --config config/walk_forward_v1.yaml --output /tmp/<report>.txt`; do not write to `vela.db` without separate explicit authorization
- [x] 7.3 Verify the complete report contains exact window boundaries, best parameters, deterministic OOS versions, train/OOS metrics, skip summary, aggregate statistics, parameter stability, and equal-weight annualized-return/Sharpe differences; do not require a predetermined market outcome
- [x] 7.4 Compare source-row counts before/after an integration run to prove training search adds no source signals/runs/curves and only expected OOS/baseline runs are persisted to the temporary target
