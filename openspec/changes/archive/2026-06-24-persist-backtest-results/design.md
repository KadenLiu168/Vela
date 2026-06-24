## Context

The project already has ORM models for `BacktestRun` and `BacktestEquityCurve`, including metric columns, parameter JSON, and an equity-curve relationship. Previous COPs added calculation helpers for equity curve points and metrics, but there is no service that persists a completed backtest result.

The user selected two Explore decisions for COP-64: implement only a result persistence helper, not a backtest runner; and create a new run per persistence call, not update existing runs.

## Goals / Non-Goals

**Goals:**

- Persist one backtest result as a new `BacktestRun`.
- Persist caller-provided curve row inputs as `BacktestEquityCurve` rows linked to that run.
- Return the created run and curve rows to callers.
- Provide a query helper that loads a run by id with its curve rows.

**Non-Goals:**

- Do not compute equity curve rows, cash, market value, total assets, or positions JSON.
- Do not implement backtest execution orchestration.
- Do not update, replace, or append to existing backtest runs.
- Do not change database schema or migrations.

## Decisions

1. Add `backtest_result_persistence.py` beside existing persistence helpers.

   Rationale: `strategy_signal_persistence.py` already establishes the style for small session-based persistence functions in the core package. A dedicated module keeps COP-64 scoped to storage and query behavior.

   Alternative considered: add persistence into `strategy_equity_curve.py`. That would mix calculation with database writes and make the metric helper module less focused.

2. Accept explicit dataclass inputs for run fields, metrics, and curve rows.

   Rationale: COP-64 persists already-computed results. Dataclass inputs keep the public function typed without coupling it to any future runner output shape.

   Alternative considered: accept `StrategyConfig` and `StrategyEquityCurvePoint` directly. That would not cover required `BacktestEquityCurve` fields such as `cash`, `market_value`, `total_assets`, and `positions_json`.

3. Create a new `BacktestRun` for every persistence call.

   Rationale: The model explicitly preserves rerun history for the same strategy, config, and date range. Avoiding updates prevents undefined replacement semantics for unique curve rows.

   Alternative considered: update existing runs by id. That requires lifecycle, replace, and rollback rules that are outside COP-64.

## Risks / Trade-offs

- Callers can pass inconsistent metrics or curve data -> Keep COP-64 focused on persistence; future runner validation can own consistency.
- Empty curve rows are possible -> Allow this so failed or partial results can still preserve run metadata.
- Query ordering must be deterministic -> Order loaded curve rows by `trade_date` and `id`.
