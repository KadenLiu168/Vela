## Why

Vela currently supports only the `dual_momentum` strategy. The strategy logic is hard-wired into signal-generation and backtest orchestration: `backtest_runner.run_backtest` and `strategy_signal_service` call dual-momentum generation functions directly, while `StrategyConfig` hard-codes dual-momentum fields (`momentum`, `score_weights`, `trend_filter`, `selection`, `defense`) with `version: Literal["v1"]`. Adding a second strategy therefore requires editing shared orchestration and configuration code.

The layer below signal generation is already strategy-agnostic: holdings, equity-curve, transaction-cost, performance, persistence, and report code consume persisted target weights and prices without inspecting how a strategy chose them. This change makes the existing signal-position boundary explicit so a new strategy can be added without changing those shared capabilities.

## What Changes

- Introduce a parameter-bound `Strategy` protocol with two operations: generate target positions for one signal date from injected active ETFs and a price panel, and declare the number of prior trading sessions required as lookback. Strategies do not receive a database session.
- Keep the existing `GenerateStrategySignalResult` and persistence-callback behavior in shared signal-generation orchestration. Expected strategy failures use a project-owned `StrategyGenerationError`; the shared wrapper converts them to the existing failed-result contract, while unexpected programming errors continue to raise.
- Introduce a plain registry mapping a config `type` to a factory that binds that type's validated parameters and returns a `Strategy`. There is no plugin auto-discovery or dynamic import.
- Restructure strategy configuration as a top-level Pydantic discriminated union: each variant has common fields (`strategy_id`, `version`, `universe_config`, `rebalance`, `costs`, `performance`), a literal `type`, and a typed `parameters` model. This is a top-level union because Pydantic cannot discriminate a `parameters` field using a sibling `type` field.
- Migrate the existing dual-momentum logic behind the protocol without changing its calculations, fallback rules, persistence behavior, or public generic signal-generation entry-point names.
- Add a minimal `equal_weight` strategy as the second implementation. It assigns `1/N` to every caller-supplied active ETF, requires no price history, and uses the same rebalance, persistence, holdings, equity-curve, and reporting paths.
- Refactor the backtest and live signal paths to dispatch through the registry. Backtest price-panel sizing uses the bound strategy's `lookback_days()` instead of reading dual-momentum fields.
- **BREAKING config change**: migrate `config/strategy_v1.yaml` to `type` + `parameters`. The loader rejects the legacy flat shape with a migration message. `version` becomes any non-empty string.
- **API response change**: strategy details returned by `/api/config` and `/api/dashboard` include `type` and nest strategy-specific values under `parameters`. The web client and Dashboard are adapted in this change so both registered strategy types render safely.
- Preserve the existing persistence schema. Because stored signals and runs are identified by `(strategy_id, config_version)` and do not store `type`, changing strategy type or behavior MUST also use a distinct identity pair (normally a type-specific `strategy_id`, and a new version for parameter changes).

## Capabilities

### New Capabilities
- `strategy-pluggability`: protocol, expected-error contract, registry/factory dispatch, uniform position output, and the four code touchpoints required to add a strategy.

### Modified Capabilities
- `strategy-configuration`: top-level discriminated config variants, nested typed parameters, non-empty string versions, legacy-shape rejection, identity rules, and the serialized API shape.
- `strategy-signal-generation`: shared result/persistence orchestration dispatches to a bound strategy and preserves current success/failure semantics without strategy-specific branches.
- `backtest-execution`: strategy-declared lookback sizes the price panel; historical generation invokes the same protocol per rebalance date.

## Impact

- **Core code**: add `packages/core/src/vela_core/strategies/`; update `strategy_config.py`, `strategy_signal_generation.py`, `momentum_scoring.py`, `trend_filter.py`, `backtest_runner.py`, `strategy_signal_service.py`, and affected exports/type annotations.
- **Python API**: generic generation names and result/position imports remain available, but the strategy-specific `defense_lookup` argument is removed. Direct schema validation moves from `StrategyConfig.model_validate(...)` to the exported strategy-config TypeAdapter/helper because `StrategyConfig` becomes a union type.
- **Config**: `config/strategy_v1.yaml` is migrated in place. The old flat structure is intentionally unsupported after this change.
- **API/web**: update `apps/api/src/vela_api/config.py`, API contract tests, `apps/web/src/api/client.ts`, and the Dashboard's type-specific strategy rendering. No endpoints or CLI subcommands are removed.
- **Database**: no migration. `strategy_signal` and `backtest_run` continue to use `strategy_id` + `config_version` as the persisted strategy identity.
- **Tests**: preserve all dual-momentum behavior; add config-union, registry, error-boundary, equal-weight, lookback, identity-isolation, API, web, and config-only switching coverage.
- **Unaffected**: holdings/equity formulas, T+1 effectiveness, transaction-cost and performance calculations, signal/backtest persistence schema and transaction ownership, report export, market-data projection, trading calendar, and data-quality checks.

## Out of Scope

- Auto-discovery, Python entry points, dynamic imports, or a plugin marketplace.
- Running multiple strategies in one backtest run.
- Adding a `strategy_type` database column or fixing pre-existing concurrent same-identity backtest read isolation.
- Portfolio optimization, order execution, or real-time trading.
