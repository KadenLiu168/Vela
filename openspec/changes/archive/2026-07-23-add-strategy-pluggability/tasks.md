## 1. Configuration union and migration contract

- [x] 1.1 Add failing config tests for dual/equal variants, missing/unknown type, non-empty version, nested field paths, forbidden mixed legacy fields, empty equal-weight params, and targeted legacy-shape errors
- [x] 1.2 Introduce common config fields, `DualMomentumParams`, `EqualWeightParams`, the two literal top-level config variants, and the top-level discriminated union/TypeAdapter; keep models frozen and forbid unknown fields
- [x] 1.3 Adapt YAML loading to validate the TypeAdapter while preserving path-rich `ConfigError` for read, parse, and validation failures
- [x] 1.4 Make defensive-universe validation run only for the dual-momentum variant and report `parameters.defense.assets[i]`
- [x] 1.5 Migrate `config/strategy_v1.yaml` to `type: dual_momentum` plus nested `parameters`; update `app_config.py` typing without changing ETF-pool loading
- [x] 1.6 Update existing config fixtures/tests to the nested shape and verify all pre-change validation rules still pass/fail equivalently
- [x] 1.7 Export and test the supported direct validation entry point (TypeAdapter/helper), and update callers that previously used `StrategyConfig.model_validate(...)`

## 2. Protocol, position type, registry, and error boundary

- [x] 2.1 Add failing tests for factory resolution, parameter binding, unsupported direct registry lookup, expected-error conversion, unexpected-error propagation, empty-active failure, empty-position success, and callback invocation count
- [x] 2.2 Define the bound `Strategy` protocol (`lookback_days`, single-date `generate_signal`) and `StrategyGenerationError`
- [x] 2.3 Relocate or re-export `GeneratedSignalPosition` so strategies and existing public imports use the same class without circular imports
- [x] 2.4 Implement the immutable plain-dict strategy factory registry and `resolve_strategy(config)` with no runtime mutation/discovery API
- [x] 2.5 Keep `generate_strategy_signal` as shared result/persistence orchestration and make it dispatch through the registry; remove its strategy-specific `defense_lookup` parameter
- [x] 2.6 Keep `generate_historical_strategy_signals` as the shared rebalance loop using the generic single-date wrapper, preserving ordering, no-future-data truncation, and per-result callbacks

## 3. Dual-momentum migration with behavioral parity

- [x] 3.1 Add/retain failing golden tests covering trend pass/fail, insufficient history, rankings/ties, Top N, multi-asset defensive fallback, missing defense, empty result, no-future-data, result labels, and persisted callback payloads
- [x] 3.2 Implement `strategies/dual_momentum.py` as a parameter-bound strategy using the existing pure calculations and deriving defense lookup from `active_etfs`
- [x] 3.3 Change `momentum_scoring.py` and `trend_filter.py` helpers to accept `DualMomentumParams` or narrower nested models instead of the monolithic config; do not change formulas or adjusted-price behavior
- [x] 3.4 Implement dual-momentum lookback as `max(short_window_days, long_window_days, moving_average_days)` prior sessions
- [x] 3.5 Register `dual_momentum` and make all updated pre-change dual-momentum regression tests pass with unchanged expected behavior

## 4. Strategy-agnostic live and backtest orchestration

- [x] 4.1 Add failing service tests proving live generation uses registry dispatch, constructs no defense lookup, preserves source validation, and retains current commit/callback behavior
- [x] 4.2 Refactor `strategy_signal_service.generate_and_persist_strategy_signal` to call generic generation with only config, active ETFs, and price panel
- [x] 4.3 Add failing backtest tests for resolved lookback, zero lookback, negative lookback rejection before persistence, generic historical dispatch, and absence of type-specific branches/imports
- [x] 4.4 Refactor `backtest_runner` to resolve the bound strategy for lookback, preserve the existing calendar conversion (`lookback * 2 + 10`), and use generic historical generation
- [x] 4.5 Preserve backtest signal-id capture/linkage, caller-managed transaction behavior, holdings/equity/metric calls, data-quality checks, and `parameters_json`; include strategy `type` in `parameters_json` for auditability without changing DB schema
- [x] 4.6 Update affected core exports, annotations, CLI/API test doubles, and direct in-repo callers for the removed `defense_lookup` argument

## 5. Equal-weight validation strategy

- [x] 5.1 Add failing unit tests for deterministic ETF-id order, one position per active ETF, exact `Decimal("1") / Decimal(N)` weights, null rank/score, ignored empty price panel, and lookback 0
- [x] 5.2 Implement and register parameter-bound `strategies/equal_weight.py` with no price-panel reads or strategy-specific persistence logic
- [x] 5.3 Add integration tests showing empty active input is the shared failed result and non-empty equal weight succeeds through live and historical generic generation

## 6. Persisted identity isolation and config-only switching

- [x] 6.1 Add config fixtures for dual momentum and equal weight with distinct `(strategy_id, version)` pairs
- [x] 6.2 Add an end-to-end switching test that runs the same date range with each config and proves both use unchanged downstream code
- [x] 6.3 Assert signals, holdings, equity calculations, and backtest rows for the two identity pairs do not select each other's persisted rows
- [x] 6.4 Document beside the config identity fields that type changes require a distinct identity pair and parameter changes require a new version; do not add a DB migration

## 7. API serialization and in-repo web consumer

- [x] 7.1 Add failing API tests for `/api/config` and `/api/dashboard` with both config variants and the common + `type` + `parameters` response shape
- [x] 7.2 Update `_serialize_config` to emit common fields plus the selected variant's nested parameters without dual-momentum-only top-level keys
- [x] 7.3 Update the web `DashboardStrategySummary` to a discriminated union on `type`
- [x] 7.4 Update Dashboard rendering to always show common fields, show dual-momentum rows only for that variant, and render equal weight without accessing missing fields
- [x] 7.5 Update web client/component fixtures and tests for both strategy types; confirm the current dual-momentum UI retains its information

## 8. Verification and quality gates

- [x] 8.1 Run targeted core config/registry/generation/service/backtest tests and API/web contract tests
- [x] 8.2 Run the full Python pytest suite; verify all pre-change dual-momentum expectations remain behaviorally green
- [x] 8.3 Run `ruff check`, `ruff format --check`, and `mypy` for the configured Python source roots
- [x] 8.4 Run the web repository's existing typecheck/lint/test commands from `apps/web/package.json`
- [x] 8.5 Verify by search that backtest_runner, strategy_signal_service, and generic signal-generation orchestration import no concrete strategy and contain no strategy-type-specific conditionals
- [x] 8.6 Verify no Alembic migration or persistence-schema change was introduced and record the known same-identity concurrent-backtest read-isolation risk as out of scope
- [x] 8.7 Run `openspec validate add-strategy-pluggability --strict`
