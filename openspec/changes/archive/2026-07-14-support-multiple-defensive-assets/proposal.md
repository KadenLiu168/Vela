## Why

The current strategy configuration models the defensive asset as a single `ETFIdentity` on `DefenseConfig.asset`. There is no way to express several defensive (safe-haven) assets at once, so a fallback can only ever allocate 100% to one ETF. Supporting a list of defensive assets lets the fallback spread the safe-haven allocation across multiple low-volatility ETFs (e.g. a bond ETF plus a money-market ETF), improving diversification of the defensive sleeve while keeping the existing all-or-nothing fallback semantics.

## What Changes

- Change `DefenseConfig.asset` (single `ETFIdentity`) to `DefenseConfig.assets` (a list of `ETFIdentity`).
- Require at least one asset (`min_length=1`); an empty list is rejected at schema validation.
- Reject duplicate `(exchange, symbol)` entries in `defense.assets` at schema validation.
- Update `_validate_defensive_asset` to validate every configured asset is an active ETF in the referenced universe, with the error message referencing `defense.assets[i]`.
- Update `select_with_defensive_fallback` to return one `DefensiveFallbackSelection` per configured defensive asset, in `defense.assets` configuration order, each carrying an equal target weight of `Decimal("1") / Decimal(N)` (N = number of assets). Single-asset configuration is a supported degenerate case that yields weight `1.0` exactly (unchanged behavior). The sum of fallback target weights is always `1.0` within Decimal rounding tolerance (`abs(sum - 1) < 1e-9`); for N > 1 it is approximately, not exactly, `1.0`.
- Update `generate_strategy_signal` resolution: each fallback selection is resolved via the caller-supplied `defense_lookup` (which already covers all active ETFs); the failure message is updated to name the specific missing `(exchange, symbol)` — i.e. the `DefensiveFallbackSelection` whose `defense_lookup` lookup returned `None`. The message always refers to a single concrete asset (use `selection.exchange` / `selection.symbol`), never a generic plural and never the whole `defense.assets` list. If more than one defensive asset is missing, the first one encountered in `defense.assets` configuration order triggers the failure and is the one named.
- Update `config/strategy_v1.yaml`: `defense.asset` becomes `defense.assets` (a list) with three entries - `SSE 511010` (国债ETF), `SSE 511880` (银华日利ETF), `SSE 518880` (黄金ETF) - each receiving equal fallback weight `1/3`.
- Update the `/config` and `/dashboard` API response shape (`defense.asset` -> `defense.assets`); both endpoints serialize the same `defense.model_dump()`. This is a direct breaking change with no backward-compatibility shim. On the web side, update the `DashboardResponse.defense` type in `apps/web/src/api/client.ts` (`asset` -> `assets` list), the `formatDefensiveAsset` helper and its call site in `apps/web/src/pages/DashboardPage.tsx` (render the list), and every typed `DashboardResponse` mock that currently uses `defense: { asset: { ... } }` - `apps/web/src/api/client.test.ts`, `apps/web/src/App.test.tsx`, `apps/web/src/components/CommandPalette.test.tsx`, `apps/web/src/components/CommandPalette.stories.tsx` - so the mocks still compile against the new `defense.assets` list shape.
- Update tests in the core package and the API to use the new `defense.assets` list shape and assert list-shaped fallback output. `packages/core/tests/test_bootstrap.py` and `apps/api/tests/test_bootstrap_endpoint.py` construct `DefenseConfig` directly and move to `assets=[...]`; `packages/core/tests/test_momentum_scoring.py`, `packages/core/tests/test_strategy_signal_generation.py`, `packages/core/tests/test_backtest_runner.py`, `packages/core/tests/test_trend_filter.py`, and `packages/core/tests/test_strategy_equity_curve.py` build `StrategyConfig` via `model_validate` over a dict, so their `defense` dict key moves from `{"asset": {...}}` to `{"assets": [...]}`. `apps/api/tests/test_api_config.py` asserts the `/api/config` `defense` response shape and moves from `{"asset": {...}}` to `{"assets": [...]}`. The checked-in `config/strategy_v1.yaml` lists three defensive assets (`511010`, `511880`, `518880`); all three already exist active in `config/etf_pool.yaml` (loader validation needs no `etf_pool.yaml` change), but `apps/api/tests/test_backtest_run.py` must `add_etf` the two new assets (`511880`, `518880`) in its temp DB so runtime `defense_lookup` can resolve them. `tests/integration_data.py` needs no change - `seed_minimal_workflow_data` does not load `strategy_v1.yaml` or build `defense_lookup`. The CLI needs no change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `momentum-scoring`: Extend the defensive fallback selection requirement to apply all configured defensive assets with equal split target weights.
- `strategy-configuration`: Extend the defensive asset identity requirement to a list of one or more unique active ETFs, and update the v1 config parameter-group scenario to reference a `defense.assets` list.
- `strategy-signal-generation`: Update the defensive fallback scenarios to reflect multiple target positions with equal split weights and missing-asset failure handling that names the specific missing `(exchange, symbol)`.

## Impact

- `packages/core/src/vela_core/strategy_config.py`
- `packages/core/src/vela_core/momentum_scoring.py`
- `packages/core/src/vela_core/strategy_signal_generation.py`
- `apps/api/src/vela_api/config.py` (serialization follows `model_dump`, no logic change)
- `apps/web/src/pages/DashboardPage.tsx` (`formatDefensiveAsset` helper, list rendering)
- `apps/web/src/api/client.ts` (`DashboardResponse.defense` type: `asset` -> `assets` list; this is where the `DashboardResponse` type actually lives, so omitting it breaks the web contract/compile)
- `apps/web/src/api/client.test.ts` (`defense` mock: `asset` -> `assets` list)
- `apps/web/src/App.test.tsx` (`defense` mock: `asset` -> `assets` list)
- `apps/web/src/components/CommandPalette.test.tsx` (`defense` mock: `asset` -> `assets` list)
- `apps/web/src/components/CommandPalette.stories.tsx` (`defense` mock: `asset` -> `assets` list)
- `config/strategy_v1.yaml`
- `packages/core/tests/test_strategy_config.py`
- `packages/core/tests/test_momentum_scoring.py`
- `packages/core/tests/test_strategy_signal_generation.py`
- `packages/core/tests/test_bootstrap.py`
- `apps/api/tests/test_bootstrap_endpoint.py`
- `apps/api/tests/test_backtest_run.py`
- `apps/api/tests/test_api_config.py` (asserts `/api/config` `defense` shape: `asset` -> `assets` list)
- `packages/core/tests/test_backtest_runner.py`
- `packages/core/tests/test_trend_filter.py` (`_strategy_config` helper `defense` dict: `asset` -> `assets` list)
- `packages/core/tests/test_strategy_equity_curve.py` (`_strategy_config` helper `defense` dict: `asset` -> `assets` list)
- `tests/integration_data.py`
- `apps/cli/src/vela_cli/main.py` — **no change required**; `defense_lookup` is built as a full active-ETF map (`{(etf.exchange, etf.symbol): etf for etf in active_etfs}`), independent of `defense.asset`, so the rename does not touch this file.

## Out of Scope (recorded for future iteration)

- **Fallback position count decoupled from `top_n`**: with N defensive assets, fallback returns N positions regardless of `top_n`. This is intentional (all-or-nothing replacement of the risky allocation) but differs from the `top_n` slot count; recorded for review in a later iteration.
- **Defensive assets in the risky pool**: a defensive asset remains a normal active ETF and may still be selected as a "risky" Top N holding in non-fallback mode. Unchanged this round. If exclusion is ever desired, the correct mechanism is to keep the asset `active` and exclude its identity from the `generate_strategy_signal` scoring loop (NOT to mark it `inactive`, which would break both loader validation and `defense_lookup` resolution).
