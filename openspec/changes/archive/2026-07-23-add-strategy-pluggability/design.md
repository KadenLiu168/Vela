## Context

Today `StrategyConfig`, `strategy_signal_generation`, `backtest_runner`, and `strategy_signal_service` all know dual-momentum details. Below persisted signal positions, however, holdings, equity-curve, metrics, and reports use only `strategy_id`, `config_version`, ETF ids, target weights, and prices. The implementation seam should therefore be above `GeneratedSignalPosition`, not below persistence.

Relevant constraints from the repository:

- Python 3.11, Pydantic v2, SQLAlchemy, mypy, ruff, and pytest.
- Pure signal generation receives ORM-shaped `ETFInfo`/`MarketPrice` data but no `Session` and performs no SQL.
- `GenerateStrategySignalResult` represents expected generation failures without raising and optionally persists through a callback.
- Callers own transaction boundaries: the live service currently commits its persisted signal, while backtest persistence remains in the caller-managed transaction.
- Stored signals and downstream queries use `(strategy_id, config_version)` as the strategy identity; `type` is not stored.
- `/api/dashboard` reuses the strategy object serialized for `/api/config`, and the web Dashboard currently assumes dual-momentum-only flat fields.

## Goals / Non-Goals

**Goals:**
- Decouple strategy decisions from shared orchestration through a small protocol.
- Preserve dual-momentum calculations and existing signal result/persistence semantics.
- Prove the seam with an end-to-end `equal_weight` strategy.
- Keep configuration strongly typed per strategy.
- Make adding a strategy require four explicit, bounded code touchpoints and no changes to backtest, holdings, equity, persistence, or report flows.
- Keep both API endpoints and the Dashboard valid when the checked-in config switches strategy type.

**Non-Goals:**
- Runtime plugin discovery or third-party plugin loading.
- Multiple strategies in one run.
- A database schema change for strategy type.
- Unrelated refactors or correction of pre-existing same-identity concurrent backtest read isolation.

## Architecture and Data Flow

```text
YAML -> top-level discriminated StrategyConfig variant
                  |
                  v
       resolve_strategy(config)
       (registry factory binds parameters)
                  |
                  v
          bound Strategy instance
         /                       \
lookback_days()          generate_signal(inputs)
         |                       |
 backtest panel range     positions or StrategyGenerationError
                                 |
                                 v
             shared generate_strategy_signal wrapper
             (result creation + optional persist callback)
                                 |
             live service / historical rebalance loop
                                 |
             existing persistence, holdings, equity, reports
```

## Decisions

### D1 — Use a parameter-bound Protocol

`Strategy` is a `typing.Protocol` with:

- `lookback_days() -> int`
- `generate_signal(*, signal_date, price_panel, active_etfs) -> list[GeneratedSignalPosition]`

The registry factory receives the already validated config variant and returns an instance bound to that variant's typed `parameters`. This avoids passing a broad parameter union on every call and makes `lookback_days()` implementable without hidden global state or an ambiguous parameter argument. The protocol is structural; no inheritance or runtime plugin framework is introduced.

### D2 — Keep result, error, and persistence policy outside strategies

Strategies return only uniform positions. An expected, user/data-related strategy failure (for example a configured defensive ETF absent from the supplied active list) raises `StrategyGenerationError`. The existing shared `generate_strategy_signal` wrapper:

1. rejects an empty caller-supplied active ETF list as the existing failed result;
2. calls the bound strategy;
3. converts `StrategyGenerationError` to a failed `GenerateStrategySignalResult` and invokes the callback when supplied;
4. converts an empty position list to the existing successful `result="empty"` contract;
5. lets unexpected exceptions propagate.

This preserves the current non-raising expected-failure behavior without forcing persistence concerns into strategy implementations. It also removes the current dual-momentum-specific `defense_lookup` argument from shared entry points; the dual strategy derives that lookup from `active_etfs`.

### D3 — Reuse and relocate the uniform position type without creating a competing model

`GeneratedSignalPosition` remains the sole strategy output shape: `etf_id`, `exchange`, `symbol`, `target_weight`, optional `rank`, optional `score`. It may be defined in the strategy protocol/types module to avoid circular imports, but `vela_core.strategy_signal_generation` and existing package exports re-export the same class object. No second position DTO is added.

### D4 — Keep shared signal-generation entry points

`generate_strategy_signal` and `generate_historical_strategy_signals` remain generic public entry-point names in `strategy_signal_generation.py`. They resolve/invoke the protocol rather than containing dual-momentum logic. Historical generation retains the shared rebalance-date loop and calls the same single-date wrapper per date, preserving callback invocation, ascending order, and no-future-data behavior.

`backtest_runner` resolves the bound strategy once for `lookback_days()` and uses the generic historical entry point for generation. `strategy_signal_service` uses the generic single-date entry point. Neither module imports a concrete strategy or branches on `type`.

### D5 — Define lookback as prior trading sessions

`lookback_days()` is a non-negative count of trading sessions before the signal session. A value of 126 therefore requires up to 127 observations including the signal date, matching the existing momentum return calculation `prices[-1] / prices[-1-window] - 1`. Dual momentum returns the maximum of short momentum, long momentum, and moving-average windows. Equal weight returns 0.

Backtest converts this count to the existing safe calendar buffer (`lookback * 2 + 10` days) and still truncates each series at the signal date. The live path may continue loading history with `start_date=None`; optimizing that query is not part of this change.

### D6 — Use a top-level discriminated configuration union

Pydantic cannot discriminate the contents of a `parameters` field using a sibling `type`. The implementable shape is therefore:

- a common base containing `strategy_id`, non-empty `version`, `universe_config`, `rebalance`, `costs`, and `performance`;
- `DualMomentumStrategyConfig` with `type: Literal["dual_momentum"]` and `parameters: DualMomentumParams`;
- `EqualWeightStrategyConfig` with `type: Literal["equal_weight"]` and `parameters: EqualWeightParams`;
- a top-level `Annotated[DualMomentumStrategyConfig | EqualWeightStrategyConfig, Field(discriminator="type")]` validated through a Pydantic `TypeAdapter` (including in the YAML loader).

Top-level variants and parameter models forbid unknown fields so a partially migrated config cannot silently ignore legacy keys. `EqualWeightParams` is an explicitly empty, extra-forbidding model and YAML uses `parameters: {}`.

Because the union alias has no `.model_validate(...)` class method, direct schema callers use an exported TypeAdapter or small validation helper. The YAML loader and tests migrate to that supported entry point; the union alias remains the annotation used by orchestration and `AppConfig`.

The dual-momentum helper functions receive `DualMomentumParams` (or narrower nested parameter models) instead of the former monolithic `StrategyConfig`. Their calculations are not generalized or rewritten.

### D7 — Use a plain, closed registry

`STRATEGY_FACTORIES` maps the two literal type strings to factories. `resolve_strategy(config)` performs one lookup and binds parameters. Direct lookup of an unknown string raises a clear project-owned configuration/registry error, although normal YAML loading rejects unknown discriminator values before registry resolution.

Adding a strategy has four code touchpoints:

1. add its typed parameter model and top-level config variant to the union;
2. implement the bound `Strategy` in its own module;
3. add one registry factory mapping;
4. add focused contract/config tests and an example config fixture.

No shared orchestration or downstream capability changes are allowed for an ordinary new strategy.

### D8 — Equal weight proves the seam, not a new portfolio engine

For a non-empty supplied active ETF list, `equal_weight` returns one position per ETF with `Decimal("1") / Decimal(N)`, deterministic ETF-id order, and `rank=None`, `score=None`. It does not inspect the price panel and declares lookback 0. Empty active input is rejected by the shared wrapper before strategy invocation, matching the existing API's failed-result behavior. Decimal division may not sum exactly to 1 for all `N`; the existing Numeric persistence rounding behavior is retained.

The active list remains the database's active ETF universe used by current orchestration. Aligning database-active membership more tightly with `universe_config` is a separate concern and is not changed here.

### D9 — Preserve persisted identity semantics

No `strategy_type` column is added. Therefore `(strategy_id, config_version)` must continue to identify one immutable strategy behavior:

- switching from dual momentum to equal weight changes `type`, `parameters`, and the identity pair (normally `strategy_id: Equal_weight`, `version: v1`);
- changing parameters for an existing strategy increments `version`;
- switching back may reuse the original pair only when behavior/configuration is identical.

The config-only switching test uses distinct identity pairs and asserts the resulting signals/runs do not mix. This prevents the new feature from creating cross-type contamination in holdings/equity queries. The pre-existing possibility of concurrent runs using the same identity pair observing each other's newest signals is recorded but not expanded into this change.

### D10 — Migrate API and Dashboard together

The serialized strategy object becomes:

```text
strategy_id, version, type, universe_config,
parameters, rebalance, costs, performance
```

Both `/api/config` and `/api/dashboard` use this shape. The web type is a discriminated union on `type`. The Dashboard always renders common fields and renders momentum/selection/defense rows only for `dual_momentum`; `equal_weight` renders its type and common fields without dereferencing absent dual fields. API and web tests cover both variants.

### D11 — Hard-cut config migration with clear errors

The checked-in `strategy_v1.yaml` moves dual fields below `parameters` and adds `type: dual_momentum`. A document with a top-level `momentum` key and no `type` gets a targeted `ConfigError` pointing to the migrated file. Unknown types, mixed legacy/new fields, invalid parameters, missing files, and YAML parse failures remain path-rich `ConfigError`s.

## Failure, Transaction, and Concurrency Behavior

- Expected strategy failures produce/persist a failed signal exactly as today; unexpected exceptions are not swallowed.
- A strategy performs no SQL and never commits or flushes.
- The optional persistence callback remains the only write seam in shared generation.
- Live service transaction behavior and backtest caller-managed atomicity are unchanged.
- Registry state is module-constant after import; no runtime mutation API is introduced.
- Strategy instances hold only immutable validated parameters and are safe to create per run/request.
- Historical calculations continue trimming panel rows to `trade_date <= signal_date`.

## Risks / Trade-offs

- **Four touchpoints are not zero-touch discovery.** Accepted to retain strong validation and a simple local registry.
- **API shape is breaking.** Mitigated by updating both backend contract tests and the only in-repo web consumer in the same change.
- **No persisted strategy type.** Accepted for MVP only with the explicit immutable identity-pair rule and isolation tests.
- **Protocol is not runtime-enforced.** mypy, registry tests, and two implementations provide sufficient coverage for this repository.
- **Active DB universe can drift from the YAML pool.** Existing behavior is retained; equal weight makes it visible but this change does not redesign universe synchronization.
- **Same-identity concurrent backtests can read the latest signal by date before run linkage.** This is pre-existing. Tests for this change must use distinct identities across different strategy types; a run-scoped holdings redesign belongs in a separate change.

## Migration and Rollback

1. Add config tests and implement top-level variants/adapter plus legacy detection.
2. Add the protocol, uniform output re-export, registry, and error contract.
3. Move dual-momentum decisions behind the protocol while preserving golden behavior.
4. Make shared single-date/historical generation dispatch through the registry.
5. Wire live/backtest orchestration and strategy-declared lookback.
6. Add equal weight and config-only switching/isolation coverage.
7. Migrate YAML, API serialization, web types/rendering, and contract tests.
8. Run full Python and web quality gates.

Rollback is a code/config revert. There is no database migration to reverse, but data produced under a new identity pair remains historical data unless removed separately.
