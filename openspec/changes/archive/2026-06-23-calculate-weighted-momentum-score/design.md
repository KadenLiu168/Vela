## Context

Vela already has a validated strategy configuration with short and long momentum windows plus normalized score weights. It also has tested market-price window return logic that reads `MarketPrice.strategy_price` from SQLAlchemy storage. The missing piece is a reusable core calculation that turns the configured short and long returns into a single score for later ranking and signal generation.

## Goals / Non-Goals

**Goals:**
- Calculate one ETF's configured short and long momentum returns for an `as_of_date`.
- Combine those returns with `StrategyConfig.score_weights` into a deterministic weighted score.
- Return component returns and the combined score so future ranking code can explain results.
- Keep the calculation small, typed, and covered by unit tests.

**Non-Goals:**
- Do not implement ETF ranking, Top N selection, defensive fallback, signal persistence, or backtesting.
- Do not replace the existing fixed 20 / 60 / 120 market-price return API.
- Do not introduce a generic scoring DSL or arbitrary number of score components.

## Decisions

1. Add a narrow momentum scoring module instead of expanding `market_price_returns`.

   Rationale: fixed market-data returns and strategy-configured scoring serve different callers. A separate module keeps the existing API stable while letting strategy logic use `63/126` or any validated config windows.

   Alternative considered: change `MarketPriceReturns` to support arbitrary windows. That would broaden an existing simple data object before a second market-data caller needs it.

2. Use `StrategyConfig` as the scoring contract.

   Rationale: existing validation already guarantees positive ordered momentum windows and positive normalized score weights. The scoring code should consume that contract rather than duplicate config validation.

   Alternative considered: accept raw window and weight values. That would make tests easier to set up but would create another public parameter contract to validate and maintain.

3. Return `None` for the combined score when either component return is unavailable.

   Rationale: insufficient price history is a normal data state in the existing return calculation. Treating missing returns as zero would make data gaps indistinguishable from real flat momentum.

   Alternative considered: raise an exception for missing history. That would make routine incomplete-history scenarios harder for signal generation to handle.

## Risks / Trade-offs

- Duplicate return-window query logic could drift from the fixed return module -> Keep the helper small and mirror existing row-count and strategy-price behavior in tests.
- Decimal and float mixing can make score reproducibility unclear -> Convert configured float weights to `Decimal` using string conversion before multiplication.
- Future strategies may need more than two momentum components -> Keep this v1-specific until a concrete strategy requires a generalized scoring contract.
