## Context

Momentum scoring already calculates scores, ranks eligible ETFs, and selects configured Top N entries. Strategy configuration validates `defense.asset` as a single exchange/symbol identity and ensures that asset exists as an active ETF in the universe when loaded through the strategy config loader. Signal generation applies an all-or-nothing defensive fallback when ranked candidates cannot satisfy `selection.top_n`, allocating the full `1.0` target weight to the single defensive asset.

This change generalizes the defensive asset from a single identity to an ordered list of identities, and splits the fallback allocation equally across them.

## Goals / Non-Goals

**Goals:**

- Represent one or more defensive assets in `DefenseConfig` as a list.
- Validate the list: non-empty, unique by `(exchange, symbol)`, and each entry an active ETF in the universe.
- Split the fallback target weight equally across all configured defensive assets (total = `1.0`).
- Preserve single-asset behavior as the degenerate `N = 1` case (weight `1.0`).
- Preserve existing Top N selection when enough ranked candidates are available.
- Surface the list through the `/config` API and the web dashboard.

**Non-Goals:**

- Changing the all-or-nothing fallback trigger (`len(rankings) < top_n`).
- Changing whether a defensive asset can appear as a risky Top N holding (out of scope, recorded).
- Adding per-asset configured weights (rejected in favor of equal split).
- Keeping a backward-compatible `defense.asset` field in the API response.

## Decisions

- **D1 — List model with `min_length=1`.** `DefenseConfig.asset: ETFIdentity` becomes `DefenseConfig.assets: list[ETFIdentity] = Field(min_length=1)`. An empty list is rejected by the Pydantic schema, consistent with how other required parameter groups are rejected ("missing required strategy parameters are rejected"). Rationale: keeps the emptiness check at the schema layer rather than only in the loader.
  - Alternative considered: allow empty to mean "disable fallback". Rejected because the user requires at least one defensive asset.

- **D2 — Equal split weight.** When fallback triggers, each configured defensive asset receives target weight `Decimal("1") / Decimal(N)` (N = `len(defense.assets)`). The single-asset case yields `1 / 1 = 1.0` exactly, identical to today's `Decimal("1")`.
  - **Rounding, not exact equality.** For N > 1 the per-asset weight is a repeating Decimal rounded to the active Decimal context (prec=28). The sum of the N rounded weights is therefore *approximately* `1.0`, not exactly `1.0` — e.g. N=3 yields `0.9999…9`. This is the same behavior already exhibited by `select_top_n_etfs` (which also uses `Decimal("1") / Decimal(len(...))`), so no new risk is introduced downstream. The equity-curve and portfolio-holdings calculations already tolerate this rounding.
  - **Test assertion.** Tests MUST assert the sum within the same tolerance the project uses for score weights: `abs(sum(weights) - Decimal("1")) < Decimal("1e-9")` (see `ScoreWeightsConfig.validate_total_weight`). Do NOT assert exact equality `sum == Decimal("1.0")` and do NOT compare each weight to an exact fraction.
  - **Tolerance reference is float in the source, Decimal in the test.** `ScoreWeightsConfig.validate_total_weight` compares with *float* arithmetic (`abs(total_weight - 1.0) > 1e-9`) because `short`/`long` are floats. The defensive-weight assertion compares with *Decimal* (`abs(sum - Decimal("1")) < Decimal("1e-9")`) because the weights are `Decimal`. The magnitude (`1e-9`) is identical — only the numeric type differs. Use the `Decimal` form in the defensive-weight test; do not copy the float literal.
  - Alternative considered: per-asset configured weights. Rejected as unnecessary config surface; equal split satisfies the diversification goal and preserves the "weights sum to ~1" invariant consumed by the equity-curve and portfolio-holdings calculations.

- **D3 — Reject duplicate identities.** A `model_validator` on `DefenseConfig` rejects duplicate `(exchange, symbol)` entries. Rationale: duplicates would either double-count the same ETF or inflate the allocated weight beyond `1.0`, breaking the invariant.

- **D4 — Direct API shape break, no shim.** The `/config` and `/dashboard` endpoints serialize `defense.model_dump()`, so they automatically emit `defense.assets`. The web `DashboardResponse.defense` type (defined in `apps/web/src/api/client.ts`), the `formatDefensiveAsset` helper in `DashboardPage.tsx`, and the typed `DashboardResponse` test mocks (`client.test.ts`, `App.test.tsx`, `CommandPalette.test.tsx`, `CommandPalette.stories.tsx`) are updated to a list. No `defense.asset` compatibility alias is retained.
  - Rationale: the `http-api-service` spec does not pin the `defense.asset` shape, so this break violates no spec; a shim would only add a permanent maintenance surface.

- **D5 — `defense_lookup` construction unchanged.** `defense_lookup` is already `{(etf.exchange, etf.symbol): etf for etf in active_etfs}` — a full active-ETF map, not a defense-only map. Multiple fallback selections resolve through it without change; only the selection cardinality and the failure message change.

- **D6 — `DefensiveFallbackSelection` unchanged.** The dataclass already represents a single asset. The selection function simply returns one instance per configured asset, in `defense.assets` configuration order, so the fallback output is deterministic and assertable in tests (`selections[i].exchange/symbol` map to `defense.assets[i]`). No structural change to the type. Each instance carries `rank=None`, `score=None`, and `target_weight=Decimal("1")/Decimal(N)`.

- **D7 — Out-of-scope items recorded, not implemented.** Fallback count vs `top_n` decoupling (D7a) and defensive-asset-in-risky-pool exclusion (D7b) are documented in the proposal's Out of Scope section for future iteration. Notably, excluding a defensive asset from the risky pool must be done by keeping it `active` and filtering its identity out of the `generate_strategy_signal` scoring loop — NOT by marking it `inactive`, which would break both loader validation (`_validate_defensive_asset` requires active) and `defense_lookup` resolution.

## Risks / Trade-offs

- **Fallback returns N positions, not `top_n`.** With N defensive assets the fallback produces N target positions regardless of `top_n`. This is inherent to the all-or-nothing allocation and is recorded as a future-review item (D7a).
- **Weight is a repeating Decimal for N > 1.** `Decimal("1") / Decimal(N)` is rounded to the active Decimal context (prec=28). The sum `N * (1/N)` is approximately `1.0` but NOT exactly equal for all N (e.g. N=3 yields `0.9999…9`, N=6 yields `1.0000…2`). Tests must assert `abs(sum(weights) - Decimal("1")) < Decimal("1e-9")` (matching the `ScoreWeightsConfig` tolerance), not exact equality, and must not compare each weight to an exact fraction. This rounding is already present in `select_top_n_etfs`, so it introduces no new downstream risk.
- **Broad test churn.** Many tests construct `DefenseConfig(asset=...)`; all must move to `assets=[...]`. This is mechanical but touches core, API, and integration fixtures. The CLI needs no change (no CLI test constructs `DefenseConfig`, and `defense_lookup` is independent of `defense.asset`); web changes span the `DashboardResponse.defense` type, the `formatDefensiveAsset` helper, and the typed `DashboardResponse` test mocks (`client.test.ts`, `App.test.tsx`, `CommandPalette.test.tsx`, `CommandPalette.stories.tsx`) - all move from `defense.asset` to `defense.assets` to keep compiling.
- **`defense_lookup` is built once from the current active-ETF set.** Both backtest and signal generation build `defense_lookup` from the `active_etfs` passed in (a single snapshot), then reuse it across all rebalance dates. If any configured defensive asset is `inactive` on a historical date that the snapshot still treats as active, that day's fallback resolves to a missing asset and fails. This risk already exists for the single-asset case and is **amplified** by N defensive assets (any one being inactive fails the day). The change does not alter `defense_lookup` construction (D5), so this is a pre-existing latent risk, not a regression; record it for a future iteration that builds per-date active lookups.
