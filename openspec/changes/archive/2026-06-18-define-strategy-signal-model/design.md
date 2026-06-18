## Context

Vela already has SQLAlchemy ORM models for ETF metadata, daily market prices, and data fetch logs. Strategy signal generation is in Phase 1 scope, but there is not yet a durable model for recording generated signals or their target positions.

The model should support future strategy services and backtests without assuming real-time trading, broker integration, or complex portfolio optimization.

## Goals / Non-Goals

**Goals:**

- Define a durable record for each strategy signal generation run.
- Preserve multiple runs for the same signal date and configuration version.
- Store target ETF position details in a queryable child table.
- Keep the model style consistent with the existing SQLAlchemy 2.0 typed ORM models.
- Expose the models through `Base.metadata` for Alembic migration generation.

**Non-Goals:**

- Implement strategy calculation logic.
- Implement portfolio optimization, order generation, or broker integration.
- Define repository or service-layer APIs for querying the latest successful signal.
- Enforce all status/result lifecycle rules in database constraints.

## Decisions

1. Model `StrategySignal` as a generation run, not only the final daily signal.

   Rationale: The system needs to preserve failed attempts, retries, and reruns after data corrections. A unique constraint on `signal_date` and `config_version` would erase or reject useful run history.

   Alternative considered: store only one final signal per date and config version. This is simpler for lookup, but loses execution history and makes failed generation diagnostics harder.

2. Split execution state from strategy judgement.

   Rationale: `status` records whether the generation task is running, succeeded, failed, or partially completed. `result` records the strategy judgement when one exists. This keeps `failed` execution separate from a successful `empty` strategy result.

   Alternative considered: use one result field for both task status and strategy output. That overloads the field and makes failures ambiguous.

3. Store positions in `StrategySignalPosition`.

   Rationale: Position details need ETF foreign keys, target weights, and optional explanation fields that should be queryable by signal and ETF. A normalized child table also supports uniqueness for each ETF within one signal.

   Alternative considered: store positions as JSON text on `StrategySignal`. This would be smaller initially, but weaker for constraints and future backtest queries.

4. Keep `rank` optional and non-unique.

   Rationale: Early strategies may omit ranks or produce tied ranks. `score` and `target_weight` still allow backtests and diagnostics to use the position output.

   Alternative considered: enforce unique rank per signal. This produces cleaner strict rankings, but prematurely constrains strategies that allow ties or do not rank every position.

5. Use string value sets in the model, not database enums.

   Rationale: Existing models use string fields with `ClassVar` allowed values. Keeping this pattern avoids introducing enum migration complexity before lifecycle services exist.

   Alternative considered: database enum or check constraints. This gives stronger enforcement, but adds portability and migration friction in the current SQLite-oriented foundation.

## Risks / Trade-offs

- Latest successful signal lookup will require ordering by `generated_at` because duplicate date/config runs are allowed -> Mitigation: add indexes for `signal_date/config_version` and `status/generated_at`.
- Status/result consistency is not fully enforced by the database -> Mitigation: document supported values and add model tests; lifecycle validation can be added with generation services.
- Optional non-unique ranks can represent less structured output -> Mitigation: preserve `score` and `target_weight` as the core position semantics.
