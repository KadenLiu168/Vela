## Context

Vela already defines `StrategySignal` and `StrategySignalPosition` ORM models. Those models intentionally preserve run history by allowing multiple rows for the same `signal_date` and `config_version`, but callers still need a focused core API to write one signal with its positions and to read the latest successful signal for downstream workflows.

COP-52 is a persistence step only. It should not implement signal generation, CLI entrypoints, schema migrations, backtesting, or later COP work.

## Goals / Non-Goals

**Goals:**

- Provide a small core helper for persisting one strategy signal run and its target positions.
- Make repeated same-date generation behavior explicit: each call creates a new run history row.
- Provide a query helper for the latest successful signal by `signal_date` and `config_version`.
- Keep implementation and tests close to existing SQLAlchemy patterns.

**Non-Goals:**

- Change the strategy signal database schema.
- Generate strategy selections from market data or momentum scores.
- Add CLI commands or application workflow orchestration.
- Enforce lifecycle transitions beyond the existing model value sets.

## Decisions

1. Add a dedicated `strategy_signal_persistence.py` module.

   Rationale: Existing modules keep focused behavior in small core files such as market price upsert and market data fetching. A dedicated module avoids expanding ORM model files with service behavior.

   Alternative considered: place helpers in `models/strategy_signal.py`. That would couple persistence workflow code to model definitions and make future query helpers harder to keep organized.

2. Preserve run history instead of upserting by date and config version.

   Rationale: The existing `strategy-signal-model` contract explicitly allows same date/config reruns so failed attempts, retries, and data-correction reruns remain auditable. COP-52 only needs the behavior to be clear and queryable.

   Alternative considered: delete or overwrite the previous same-date signal. That would make "latest" storage simpler, but would conflict with the run-history model.

3. Query latest successful signal using `generated_at` descending with `id` descending as a deterministic tie-breaker.

   Rationale: `generated_at` is the domain timestamp for signal generation. `id` handles tests and edge cases where two persisted rows share the same timestamp.

   Alternative considered: order only by `created_at`. That reflects database insert time, not the signal generation time already modeled.

4. Accept position input as simple dataclasses with `etf_id`, `target_weight`, optional `rank`, and optional `score`.

   Rationale: COP-50/51 selection outputs are not the only possible future source of positions. A minimal persistence input avoids coupling this change to momentum selection internals.

   Alternative considered: accept `TopNSelection` and `DefensiveFallbackSelection` directly. That would prematurely bind persistence to current selection types and still requires resolving defensive assets to database IDs outside this helper.

## Risks / Trade-offs

- Callers must resolve defensive asset symbols to `etf_id` before persisting positions -> Mitigation: keep COP-52 scoped to persisted IDs and leave symbol resolution to signal generation orchestration.
- The helper does not commit the session -> Mitigation: match existing core patterns where callers own transaction boundaries.
- Latest query ignores failed, running, and partial signals -> Mitigation: this matches the acceptance criterion for a queryable latest usable result while preserving all rows for audit.
