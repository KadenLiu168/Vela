## Context

`StrategySignal` and `StrategySignalPosition` already exist as SQLAlchemy ORM models. `StrategySignalPosition.strategy_signal_id` enforces the database relationship, but Python code does not yet have a first-class ORM relationship for navigating from a signal run to its positions or from a position back to its signal run.

## Goals / Non-Goals

**Goals:**

- Make the existing signal-to-position relationship explicit at the SQLAlchemy ORM object level.
- Preserve the existing model name, table name, columns, indexes, and constraints.
- Keep implementation small and covered by focused ORM tests.

**Non-Goals:**

- Do not rename `StrategySignalPosition` to `SignalPosition`.
- Do not add a database migration.
- Do not add delete cascade behavior.
- Do not change ETF relationship behavior.

## Decisions

- Add `StrategySignal.positions` and `StrategySignalPosition.strategy_signal` using SQLAlchemy `relationship(..., back_populates=...)`.
  - Rationale: the foreign key protects database integrity, while ORM relationships make the association directly navigable in backend code.
  - Alternative considered: keep only `strategy_signal_id`. This is simpler but leaves callers to write manual lookups and does not satisfy the "explicit association" intent.
- Keep `StrategySignalPosition` as the public ORM model name.
  - Rationale: the name matches the existing table and clearly scopes positions to strategy signal runs.
  - Alternative considered: introduce `SignalPosition` as a new name or alias. That adds API surface without a clear need after the issue wording is clarified.
- Do not configure cascade delete.
  - Rationale: deleting historical signal runs and their positions is a data retention policy decision. This change only makes the relationship explicit.

## Risks / Trade-offs

- Lazy relationship loading can introduce extra queries if callers iterate many signals and access `positions` one by one. Mitigation: keep default ORM behavior for now and let query code choose eager loading when needed.
- Relationship attribute names become part of the public model API. Mitigation: use direct, conventional names: `positions` and `strategy_signal`.
